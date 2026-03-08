#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.22 — Global Header Patches

═══════════════════════════════════════════════════════════════════════════════
LOG 46 — v75.21 successfully fixed Pass 2 & 4. New SDK/Clang strictness errors:
  1. stub_3A70.c: error: use of undeclared identifier 'G_TRI2'
  2. animation.h: error: unknown type name 'size_t'
═══════════════════════════════════════════════════════════════════════════════

ROOT CAUSE & FIX:
  1. `G_TRI2` requires the F3DEX2 microcode macro. CMake is likely missing 
     `-DF3DEX_GBI_2`. Fix: Inject `#define F3DEX_GBI_2 1` into `gbi.h`.
  2. Clang is strict about standard types. `animation.h` uses `size_t` without
     the proper include. Fix: Inject `#include <stddef.h>` into `animation.h`.
     
  We introduce a "Pass 0" to precisely patch these specific header files before 
  the main C-file harmonization loop begins.
"""

class SourceHarmonizerV7522:
    def __init__(self, target_dir, decomp_path):
        self.target_dir  = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0}

        self.c_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
            'break', 'continue', 'case', 'default', 'goto', 'struct', 'union',
            'enum', 'static', 'extern', 'const', 'volatile', 'inline', 'typedef'
        }

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

        self._p3a = re.compile(r'^([ \t]+)static\s+([^=\n;{}]+?)\s*([|&^+\-*/%]=|<<=|>>=)', re.MULTILINE)
        self._p3a2 = re.compile(r'^([ \t]+)static\s+([a-zA-Z_]\w*(?:->|\.)[^=\n;{}]*?)\s*=\s*([^;\n]+?)\s*;[^\n]*$', re.MULTILINE)
        self._p3b = re.compile(r'^([ \t]+)static\s+([a-zA-Z_]\w*)\s*=\s*([^;\n]+(?:\([^;\n]*\))[^;\n]*)\s*;[^\n]*$', re.MULTILINE)
        self._p3c = re.compile(r'^([ \t]+)static\s+([^=\n;{}]+?)\b([a-zA-Z_]\w*)\s*=\s*([^;\n]+)\s*;[^\n]*$', re.MULTILINE)

        self._def_pat_cache = {}

    def setup_workspace(self):
        print("[>] Preparing v75.22 Workspace...")
        for folder in [self.target_dir / "src", self.target_dir / "include"]:
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
        for sub in ["src", "include"]:
            src = self.decomp_path / sub
            dst = self.target_dir / sub
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)

    def patch_global_headers(self):
        """Pass 0: targeted patches for N64/Clang compatibility missing from CMake"""
        
        # 1. Fix G_TRI2 errors globally
        gbi_path = self.target_dir / "include" / "2.0L" / "PR" / "gbi.h"
        if gbi_path.exists():
            content = gbi_path.read_text(encoding='utf-8', errors='ignore')
            if 'F3DEX_GBI_2' not in content[:500]:
                gbi_path.write_text("#ifndef F3DEX_GBI_2\n#define F3DEX_GBI_2 1\n#endif\n" + content, encoding='utf-8')
                self.stats["changes_made"] += 1
                
        # 2. Fix size_t missing type globally
        anim_path = self.target_dir / "include" / "animation.h"
        if anim_path.exists():
            content = anim_path.read_text(encoding='utf-8', errors='ignore')
            if '<stddef.h>' not in content:
                anim_path.write_text("#include <stddef.h>\n" + content, encoding='utf-8')
                self.stats["changes_made"] += 1

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
            fwd_pat = re.compile(
                r'^([ \t]*)([a-zA-Z0-9_\s\*]*?\b)' + re.escape(func_name) + r'\s*\([^;{}]*\)\s*;',
                re.MULTILINE
            )
            
            def _fwd_repl(m):
                full = m.group(0)
                indent = m.group(1)
                prefix = m.group(2)
                
                if re.search(r'\bstatic\b', prefix): return full
                tokens = re.findall(r'[a-zA-Z_]\w*', prefix)
                if set(tokens).intersection(self._ctrl_keywords): return full
                type_toks = [t for t in tokens if t not in self._storage_quals]
                if not type_toks: return full
                    
                clean_prefix = re.sub(r'\bextern\s+', '', prefix)
                return f"{indent}static {clean_prefix}{full[len(indent)+len(prefix):]}"

            patched = fwd_pat.sub(_fwd_repl, modified)
            if patched != modified:
                modified = patched
                continue
                
            if not self.has_existing_forward_decl(clean, func_name):
                call_pat = re.compile(r'\b' + re.escape(func_name) + r'\s*\(')
                def_pat = re.compile(r'\bstatic\b[^;{}]*?\b' + re.escape(func_name) + r'\s*\([^{}]*?\)\s*\{', re.DOTALL)
                call_m = call_pat.search(clean)
                def_m = def_pat.search(clean)
                if call_m and def_m and call_m.start() < def_m.start():
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
            self._def_pat_cache[fname] = re.compile(
                r'^([ \t]*)([a-zA-Z0-9_\s\*]*?\b)(' + re.escape(fname) + r'\s*\([^;{}]*?\)\s*\{)',
                re.MULTILINE
            )
            
        def _repl(m):
            full = m.group(0)
            if '__attribute__((weak))' in full or re.search(r'\bstatic\b', m.group(2)):
                return full
            before_tokens = set(re.findall(r'[a-zA-Z_]\w*', m.group(2)))
            if before_tokens.intersection(self._ctrl_keywords):
                return full
            return f"{m.group(1)}__attribute__((weak)) {m.group(2).lstrip()}{m.group(3)}"
            
        return self._def_pat_cache[fname].sub(_repl, content)

    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        arr_pat = re.compile(r'^([ \t]*(?:struct\s+|union\s+|enum\s+)?[a-zA-Z_]\w*(?:\s*\*)*)\s+([a-zA-Z_]\w*)\s*\[\s*(\d+)\s*\]\s*=\s*([a-zA-Z_]\w*)\s*;', re.MULTILINE)
        modified = arr_pat.sub(lambda m: f"{m.group(1)} {m.group(2)}[{m.group(3)}]; __builtin_memcpy({m.group(2)}, {m.group(4)}, {m.group(3)} * sizeof({m.group(1).strip()}));", original_content)
        
        modified = self.fix_static_local_c89_patterns(self.fix_static_conflicts(modified))
        clean = self.remove_strings_and_comments(modified)
        
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
        self.patch_global_headers()
        for file_path in self.target_dir.rglob('*.[ch]'):
            if "include/libc" not in str(file_path) and file_path.suffix != '.h':
                self.process_file(file_path)
                self.stats["files_processed"] += 1
        print(f"\n[+] v75.22 Complete. Files Processed: {self.stats['files_processed']} | Modified: {self.stats['changes_made']}")

if __name__ == "__main__":
    SourceHarmonizerV7522("Android/app/src/main/cpp", "decomp-files").run()
