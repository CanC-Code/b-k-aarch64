#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.19 — Precise Weak Symbol Injection

═══════════════════════════════════════════════════════════════════════════════
LOG 42/43 — v75.18 applied `__attribute__((weak))` incorrectly to statements.
  Errors: 'weak' attribute cannot be applied to a statement
  Examples:
    __attribute__((weak)) if(func_8038D920(this, sp38[1])){
    __attribute__((weak)) chTiptup_sfxCorrectHit();
═══════════════════════════════════════════════════════════════════════════════

ROOT CAUSE:
  The Pass 4 regex `\([^{}]*?\)\s*\{` allowed matching across semicolons and 
  newlines (due to re.DOTALL and broad negative character classes). It consumed 
  function calls ending in `;` by bleeding into subsequent `if(...) {` blocks.

THE FIX:
  Tighten the definition-matching regex:
  1. Forbid `(`, `=`, `;`, `{`, `}` in the return type (Group 2).
  2. Forbid `;`, `{`, `}` inside the parameter list.
  3. Add a hard Python-level check to abort replacement if the preceding tokens
     contain control keywords (if, while, for, switch, return).
"""

class SourceHarmonizerV7519:
    def __init__(self, target_dir, decomp_path):
        self.target_dir  = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0}

        self.c_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
            'break', 'continue', 'case', 'default', 'goto', 'struct', 'union',
            'enum', 'static', 'extern', 'const', 'volatile', 'inline', 'typedef'
        }

        # Never weaken — called directly from NativeBridge.cpp / C++ layer.
        self.std_c = {
            'main', 'main_no_args',
            'memcpy', 'memset', 'strlen', 'strcpy', 'strcmp',
            'sprintf', 'printf', 'malloc', 'free',
            'sin', 'cos', 'sinf', 'cosf', 'sqrt', 'sqrtf', 'abs', 'fabs'
        }

        self.sdk_prefixes = ('os', 'gu', 'al', 'gS', 'gD', 'gd', '__os', 'sp', 'dp', 'rmon')

        self._storage_quals = {
            'static', 'extern', 'inline', 'const', 'volatile', '__attribute__',
            '__restrict', 'restrict', 'register'
        }
        
        self._ctrl_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
            'break', 'continue', 'case', 'default', 'goto', 'typedef'
        }

        # Pass 3 patterns (C89/IDO static-local normalization)
        self._p3a = re.compile(r'^([ \t]+)static\s+([^=\n;{}]+?)\s*([|&^+\-*/%]=|<<=|>>=)', re.MULTILINE)
        self._p3a2 = re.compile(r'^([ \t]+)static\s+([a-zA-Z_]\w*(?:->|\.)[^=\n;{}]*?)\s*=\s*([^;\n]+?)\s*;[^\n]*$', re.MULTILINE)
        self._p3b = re.compile(r'^([ \t]+)static\s+([a-zA-Z_]\w*)\s*=\s*([^;\n]+(?:\([^;\n]*\))[^;\n]*)\s*;[^\n]*$', re.MULTILINE)
        self._p3c = re.compile(r'^([ \t]+)static\s+([^=\n;{}]+?)\b([a-zA-Z_]\w*)\s*=\s*([^;\n]+)\s*;[^\n]*$', re.MULTILINE)

        self._def_pat_cache = {}

    def setup_workspace(self):
        print("[>] Preparing v75.19 Workspace...")
        for folder in [self.target_dir / "src", self.target_dir / "include"]:
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
        for sub in ["src", "include"]:
            src = self.decomp_path / sub
            dst = self.target_dir / sub
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)

    def remove_strings_and_comments(self, text):
        text = re.sub(r'//[^\n]*', '', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)
        return text

    def find_static_definitions(self, clean_content):
        static_funcs = {}
        pat = re.compile(r'\bstatic\b([^;{}]*?\b([a-zA-Z_]\w*)\s*\([^{}]*?\))\s*\{', re.DOTALL)
        for m in pat.finditer(clean_content):
            name = m.group(2)
            if name not in self.c_keywords and name not in static_funcs:
                static_funcs[name] = m.group(1).strip()
        return static_funcs

    def has_existing_forward_decl(self, clean_content, func_name):
        pat = re.compile(r'^([ \t]*(?:[^\n]*?))\b' + re.escape(func_name) + r'\s*\([^{}]*?\)\s*;', re.MULTILINE)
        for m in pat.finditer(clean_content):
            prefix = m.group(1)
            if re.search(r'[=!&|^~+\-/%<>?]', prefix) or '(' in prefix:
                continue
            tokens = re.findall(r'[a-zA-Z_]\w*', prefix)
            if [t for t in tokens if t not in self._storage_quals and t not in self._ctrl_keywords]:
                return True
        return False

    def fix_static_conflicts(self, content):
        clean = self.remove_strings_and_comments(content)
        static_defs = self.find_static_definitions(clean)
        if not static_defs: return content
        modified = content
        needs_injected = []
        for func_name, sig in static_defs.items():
            fwd_pat = re.compile(r'^([ \t]*)(?!static\b)(\b\S[^\n]*?\b' + re.escape(func_name) + r'\s*\([^)]*\)\s*;)', re.MULTILINE)
            patched = fwd_pat.sub(lambda m: f"{m.group(1)}static {m.group(2)}", modified)
            if patched != modified:
                modified = patched
                continue
            if not self.has_existing_forward_decl(clean, func_name):
                call_pat = re.compile(r'\b' + re.escape(func_name) + r'\s*\(')
                def_pat = re.compile(r'\bstatic\b[^;{}]*?\b' + re.escape(func_name) + r'\s*\([^{}]*?\)\s*\{', re.DOTALL)
                if call_pat.search(clean) and def_pat.search(clean) and call_pat.search(clean).start() < def_pat.search(clean).start():
                    needs_injected.append(f"static {sig};")
        if needs_injected:
            block = "// --- SH static forward declarations ---\n" + "\n".join(needs_injected) + "\n// --- SH static forward declarations end ---\n\n"
            last_inc = None
            for m in re.finditer(r'^#include\b[^\n]*\n', modified, re.MULTILINE): last_inc = m
            pos = last_inc.end() if last_inc else 0
            modified = modified[:pos] + block + modified[pos:]
        return modified

    def fix_static_local_c89_patterns(self, content):
        content = self._p3a.sub(lambda m: f"{m.group(1)}{m.group(2).rstrip()} {m.group(3)}", content)
        content = self._p3a2.sub(lambda m: f"{m.group(1)}{m.group(2).rstrip()} = {m.group(3).strip()};", content)
        content = self._p3b.sub(lambda m: f"{m.group(1)}{m.group(2)} = {m.group(3).strip()};", content)
        content = self._p3c.sub(lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)} = {m.group(4).strip()};" if '(' in m.group(4) else m.group(0), content)
        return content

    def inject_weak_attribute(self, content, fname):
        if fname not in self._def_pat_cache:
            # Group 2 (return type): explicitly forbid ;, {, }, =, ( to prevent matching calls/assignments.
            # Group 3 (params): explicitly forbid ;, {, } to prevent bleeding across statements.
            self._def_pat_cache[fname] = re.compile(
                r'^([ \t]*)([^;{}=()]*?\b)(' + re.escape(fname) + r'\s*\([^;{}]*?\)\s*\{)',
                re.MULTILINE
            )
            
        def _repl(m):
            full = m.group(0)
            if '__attribute__((weak))' in full or re.search(r'\bstatic\b', m.group(2)):
                return full
                
            # Final safety check: if the "return type" contains control keywords, it's a false positive.
            before_tokens = set(re.findall(r'[a-zA-Z_]\w*', m.group(2)))
            if before_tokens.intersection(self._ctrl_keywords):
                return full
                
            return f"{m.group(1)}__attribute__((weak)) {m.group(2).lstrip()}{m.group(3)}"
            
        return self._def_pat_cache[fname].sub(_repl, content)

    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        # Pass 1: Array init to __builtin_memcpy
        arr_pat = re.compile(r'^([ \t]*(?:struct\s+|union\s+|enum\s+)?[a-zA-Z_]\w*(?:\s*\*)*)\s+([a-zA-Z_]\w*)\s*\[\s*(\d+)\s*\]\s*=\s*([a-zA-Z_]\w*)\s*;', re.MULTILINE)
        modified = arr_pat.sub(lambda m: f"{m.group(1)} {m.group(2)}[{m.group(3)}]; __builtin_memcpy({m.group(2)}, {m.group(4)}, {m.group(3)} * sizeof({m.group(1).strip()}));", original_content)
        
        modified = self.fix_static_local_c89_patterns(self.fix_static_conflicts(modified))
        clean = self.remove_strings_and_comments(modified)
        
        # Pass 4: Weak symbol injection
        excluded = set(self.find_static_definitions(clean).keys()) | {n for n in re.findall(r'(?<![;{}])\b([a-zA-Z_]\w*)\s*\([^{}]*?\)\s*;', clean) if n not in self.c_keywords}
        func_pat, seen = re.compile(r'\b([a-zA-Z_]\w*)\s*\([^{;]*\)\s*\{'), set()
        
        for match in func_pat.finditer(clean):
            fname = match.group(1)
            if fname in self.c_keywords or fname in self.std_c or fname.startswith(self.sdk_prefixes) or fname.isupper() or fname.startswith('__') or fname in excluded or fname in seen:
                continue
            pre = clean[:match.start()]
            cut = max(pre.rfind(';'), pre.rfind('}'), pre.rfind('{'))
            if not any(k in re.findall(r'[a-zA-Z_]\w*', pre[cut+1:] if cut != -1 else pre) for k in ('static', 'inline', 'typedef')):
                modified = self.inject_weak_attribute(modified, fname)
                seen.add(fname)

        if modified != original_content:
            with open(file_path, 'w', encoding='utf-8') as f: f.write(modified)
            self.stats["changes_made"] += 1

    def run(self):
        self.setup_workspace()
        for file_path in self.target_dir.rglob('*.[ch]'):
            if "include/libc" not in str(file_path) and file_path.suffix != '.h':
                self.process_file(file_path)
                self.stats["files_processed"] += 1
        print(f"\n[+] v75.19 Complete. Files Processed: {self.stats['files_processed']} | Modified: {self.stats['changes_made']}")

if __name__ == "__main__":
    SourceHarmonizerV7519("Android/app/src/main/cpp", "decomp-files").run()
