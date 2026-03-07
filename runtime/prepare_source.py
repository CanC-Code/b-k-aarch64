#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.5 - Guard Against Duplicate Static Forward Declaration Injection

ROOT CAUSE (v75.4 regression in attacktutorial.c):
  Strategy B of fix_static_conflicts() injected a new static forward declaration
  at the top of any file where a static function was called before its definition.
  However, attacktutorial.c already had a correct static forward declaration
  for __chAttackTutorial_setState at line 25 — after the #include block where
  the `enum ch_attack_tutorial_states` type is fully resolved.

  Strategy B did not check for existing forward declarations before injecting,
  so it inserted a DUPLICATE at the top of the file (line 5), before the enum
  definition was visible. Clang saw two conflicting declarations for the same
  function — the injected one referenced an incomplete enum type, and the
  original one at line 25 referenced the complete type — causing:
    error: conflicting types for '__chAttackTutorial_setState'
    error: argument type 'enum ch_attack_tutorial_states' is incomplete

FIX:
  has_existing_forward_decl() — new guard called at the start of Strategy B.
  If any forward declaration (static or non-static) already exists for the
  function anywhere in the file, Strategy B skips injection entirely.
  The existing declaration is already correct; no intervention is needed.

FULL PASS SUMMARY (all fixes retained):
  Pass 1 — Array init: `u8 tmp[6] = D_x;` -> __builtin_memcpy
  Pass 2 — fix_static_conflicts():
    Strategy A: patch explicit non-static forward decl -> add `static`
    Strategy B: inject static forward decl for implicit-forward cases,
                ONLY when no forward decl of any kind already exists
  Pass 3 — Build BKA exclusion set (static + forward-declared functions)
  Pass 4 — BKA macro/weak-alias injection for cross-file linking
"""

class SourceHarmonizerV755:
    def __init__(self, target_dir, decomp_path):
        self.target_dir = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0}

        self.c_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
            'break', 'continue', 'case', 'default', 'goto', 'struct', 'union',
            'enum', 'static', 'extern', 'const', 'volatile', 'inline', 'typedef'
        }

        self.std_c = {
            'main', 'main_no_args', 'memcpy', 'memset', 'strlen', 'strcpy', 'strcmp',
            'sprintf', 'printf', 'malloc', 'free', 'sin', 'cos', 'sinf',
            'cosf', 'sqrt', 'sqrtf', 'abs', 'fabs'
        }

        self.sdk_prefixes = ('os', 'gu', 'al', 'gS', 'gD', 'gd', '__os', 'sp', 'dp', 'rmon')

    def setup_workspace(self):
        print(f"[>] Preparing v75.5 Workspace...")
        src_target = self.target_dir / "src"
        include_target = self.target_dir / "include"

        for folder in [src_target, include_target]:
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)

        for sub in ["src", "include"]:
            src = self.decomp_path / sub
            dst = self.target_dir / sub
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)

    def remove_strings_and_comments(self, text):
        """Strip strings and comments for safe regex analysis."""
        text = re.sub(r'//[^\n]*', '', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)
        return text

    def find_static_definitions(self, clean_content):
        """
        Returns dict { func_name -> signature } for every function defined
        with `static` in this file. Signature = return-type + name + params,
        used to build forward declarations when needed.
        Uses re.DOTALL for reliable multiline matching.
        """
        static_funcs = {}
        pattern = re.compile(
            r'\bstatic\b([^;{}]*?\b([a-zA-Z_]\w*)\s*\([^{}]*?\))\s*\{',
            re.DOTALL
        )
        for m in pattern.finditer(clean_content):
            name = m.group(2)
            if name not in self.c_keywords and name not in static_funcs:
                static_funcs[name] = m.group(1).strip()
        return static_funcs

    def has_existing_forward_decl(self, clean_content, func_name):
        """
        Returns True if any forward declaration (static or non-static) for
        func_name already exists in the file. Used to guard Strategy B from
        injecting a duplicate that would cause 'conflicting types' errors.
        """
        pattern = re.compile(
            r'\b' + re.escape(func_name) + r'\s*\([^{}]*?\)\s*;'
        )
        return bool(pattern.search(clean_content))

    def fix_static_conflicts(self, content):
        """
        Two-strategy direct source patch for:
          'static declaration of X follows non-static declaration'

        Strategy A — patch an existing explicit non-static forward declaration:
          `void foo(Bar *x);`  ->  `static void foo(Bar *x);`
          Only applied when the non-static forward decl line exists.

        Strategy B — inject a missing static forward declaration:
          When a static function is called before its definition with NO
          existing forward decl of any kind, inject `static <sig>;` after
          the last #include so Clang has the correct type before the first call.
          GUARD: if any forward decl already exists, skip entirely to prevent
          duplicate declarations that trigger 'conflicting types' errors.
        """
        clean = self.remove_strings_and_comments(content)
        static_defs = self.find_static_definitions(clean)
        if not static_defs:
            return content

        modified = content
        needs_injected = []

        for func_name, sig in static_defs.items():
            # --- Strategy A: patch existing non-static forward decl ---
            fwd_pattern = re.compile(
                r'^([ \t]*)(?!static\b)(\b\S[^\n]*?\b'
                + re.escape(func_name)
                + r'\s*\([^)]*\)\s*;)',
                re.MULTILINE
            )
            patched = fwd_pattern.sub(
                lambda m: f"{m.group(1)}static {m.group(2)}",
                modified
            )
            if patched != modified:
                modified = patched
                continue  # Strategy A handled this function

            # --- Strategy B: inject forward decl only if none exists yet ---
            if self.has_existing_forward_decl(clean, func_name):
                # A forward decl already exists (possibly static, possibly after
                # the includes where types are complete). Do not inject a duplicate.
                continue

            # Check if function is called before its definition (implicit forward)
            call_pat = re.compile(r'\b' + re.escape(func_name) + r'\s*\(')
            def_pat  = re.compile(
                r'\bstatic\b[^;{}]*?\b' + re.escape(func_name) + r'\s*\([^{}]*?\)\s*\{',
                re.DOTALL
            )
            call_m = call_pat.search(clean)
            def_m  = def_pat.search(clean)

            if call_m and def_m and call_m.start() < def_m.start():
                needs_injected.append(f"static {sig};")

        # Inject all needed forward declarations after the last top-level #include
        if needs_injected:
            block = (
                "// --- SH static forward declarations ---\n"
                + "\n".join(needs_injected) + "\n"
                + "// --- SH static forward declarations end ---\n\n"
            )
            last_include = None
            for m in re.finditer(r'^#include\b[^\n]*\n', modified, re.MULTILINE):
                last_include = m
            if last_include:
                pos = last_include.end()
                modified = modified[:pos] + block + modified[pos:]
            else:
                modified = block + modified

        return modified

    def find_forward_declared_functions(self, clean_content):
        """
        Returns names of all functions with any forward declaration.
        These are excluded from BKA to prevent macro/alias interaction.
        """
        names = set()
        pattern = re.compile(
            r'(?<![;{}])\b([a-zA-Z_]\w*)\s*\([^{}]*?\)\s*;',
            re.DOTALL
        )
        for m in pattern.finditer(clean_content):
            name = m.group(1)
            if name in self.c_keywords:
                continue
            prefix = clean_content[:m.start()]
            cut = max(prefix.rfind(';'), prefix.rfind('{'), prefix.rfind('}'))
            segment = prefix[cut+1:] if cut != -1 else prefix
            tokens = set(re.findall(r'[a-zA-Z_]\w*', segment))
            if not tokens:
                continue
            if 'typedef' in tokens:
                continue
            names.add(name)
        return names

    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        # --- Pass 1: Fix IDO-specific array assignment ---
        # Clang rejects `u8 tmp[6] = D_80390DA0;`
        array_init_pattern = re.compile(
            r'^([ \t]*(?:struct\s+|union\s+|enum\s+)?[a-zA-Z_]\w*(?:\s*\*)*)\s+'
            r'([a-zA-Z_]\w*)\s*\[\s*(\d+)\s*\]\s*=\s*([a-zA-Z_]\w*)\s*;',
            re.MULTILINE
        )
        def array_init_repl(m):
            type_str   = m.group(1)
            name       = m.group(2)
            size       = m.group(3)
            src        = m.group(4)
            clean_type = type_str.strip()
            return (f"{type_str} {name}[{size}]; "
                    f"__builtin_memcpy({name}, {src}, {size} * sizeof({clean_type}));")

        modified_content = array_init_pattern.sub(array_init_repl, original_content)

        # --- Pass 2: Direct patch of static/forward-decl conflicts ---
        modified_content = self.fix_static_conflicts(modified_content)

        # Strip comments/strings for analysis only
        clean_content = self.remove_strings_and_comments(modified_content)

        # --- Pass 3: Build BKA exclusion set ---
        static_func_names  = set(self.find_static_definitions(clean_content).keys())
        forward_decl_names = self.find_forward_declared_functions(clean_content)
        excluded_names     = static_func_names | forward_decl_names

        fid = hashlib.md5(str(file_path.name).encode()).hexdigest()[:8]

        # Matches: func_name(...) {
        func_pattern = re.compile(r'\b([a-zA-Z_]\w*)\s*\([^{;]*\)\s*\{')

        defined_funcs = []
        for match in func_pattern.finditer(clean_content):
            func_name = match.group(1)
            start_idx = match.start()

            if func_name in self.c_keywords or func_name in self.std_c:
                continue
            if func_name.startswith(self.sdk_prefixes):
                continue
            if func_name.isupper():
                continue
            if func_name.startswith('__'):
                continue
            if func_name in excluded_names:
                continue

            # Context filter: detect static/inline/typedef on this specific definition
            prefix_str = clean_content[:start_idx]
            cut_idx = max(prefix_str.rfind(';'), prefix_str.rfind('}'), prefix_str.rfind('{'))
            if cut_idx != -1:
                prefix_str = prefix_str[cut_idx+1:]
            tokens = re.findall(r'[a-zA-Z_]\w*', prefix_str)
            if any(k in tokens for k in ['static', 'inline', 'typedef']):
                continue

            defined_funcs.append(func_name)

        # Deduplicate while preserving order
        defined_funcs = list(dict.fromkeys(defined_funcs))

        # --- Pass 4: BKA macro/alias injection ---
        macros  = ""
        aliases = ""

        if defined_funcs:
            macros  += "// --- BKA MACROS START ---\n"
            aliases += "\n\n// --- BKA ALIASES START ---\n"

            for func in defined_funcs:
                unique_name = f"BKA_F_{fid}_{func}"
                macros  += f"#define {func} {unique_name}\n"
                aliases += f"#undef {func}\n"
                aliases += (f"__typeof__({unique_name}) {func} "
                            f"__attribute__((weak, alias(\"{unique_name}\")));\n")

            macros  += "// --- BKA MACROS END ---\n\n"
            aliases += "// --- BKA ALIASES END ---\n"

        new_content = macros + modified_content + aliases

        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            self.stats["changes_made"] += 1

    def run(self):
        if not self.decomp_path.exists():
            print(f"[!] Error: Decompilation path {self.decomp_path} not found.")
            return

        self.setup_workspace()
        print(f"[*] Applying v75.5 Function-Level Linker Isolation...")

        for file_path in self.target_dir.rglob('*.[ch]'):
            if "include/libc" in str(file_path) or file_path.suffix == '.h':
                continue
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")

        print(f"\n[+] v75.5 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    target = "Android/app/src/main/cpp"
    decomp = "decomp-files"

    harmonizer = SourceHarmonizerV755(target, decomp)
    harmonizer.run()
