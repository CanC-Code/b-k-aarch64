#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.7 - Fix static local runtime-init for implicit-int C89 pattern

ROOT CAUSE (from log 27):
  The static/forward-decl errors are fully resolved (lines shifted by +5, confirming
  Strategy B injected the forward declarations successfully for code_F0.c).

  Three remaining errors are all from static local variables with runtime initializers,
  specifically the C89/IDO implicit-int form with no explicit type:
    line 69: `        static addr = __codeF0_getLearnedAbilitiesAddress();`
    line 79: `    static learned_abilities_address = __codeF0_getLearnedAbilitiesAddress();`

  v75.6's fix_static_local_runtime_init (Pass 3) used a single Form1 regex that
  required `[^=\n;{}]+?` (at least some content) between `static` and the varname.
  For implicit-int `static varname = call()`, there is NO type between `static` and
  the varname, so Form1 never matched.

FIX:
  Pass 3 now applies TWO forms in sequence:

  Form 1 — explicit type: `static u32 *addr = call();`
    Strips `static`, keeps type: `u32 * addr = call();`
    Uses original working regex: `(static\s+...+?)\b(varname)\s*=\s*([^;\n]*\([^;\n]*);$`

  Form 2 — implicit int: `static varname = call();`
    Strips `static`, converts to plain assignment: `varname = call();`
    (The variable is either declared elsewhere or this is a standalone fixup.)
    Uses regex: `static\s+(varname)\s*=\s*(rhs_with_parens);$`
    Requires RHS to contain `(...)` to avoid touching constant initialisers.

  Both forms are indentation-gated (only match inside function bodies).
  Constant initialisers like `static int count = 0;` are never touched.

FULL PASS SUMMARY (all fixes retained):
  Pass 1 — Array init:        `u8 tmp[N] = D_x;`  ->  __builtin_memcpy
  Pass 2 — Static conflicts:
    Strategy A: patch non-static forward decl          ->  add `static`
    Strategy B: inject missing static fwd decl         (guarded by type-aware decl detector)
  Pass 3 — Static local init (two forms):
    Form 1: `static TYPE var = call();`                ->  `TYPE var = call();`
    Form 2: `static var = call();` (implicit-int)      ->  `var = call();`
  Pass 4 — BKA exclusion set: static + forward-declared functions excluded
  Pass 5 — BKA macro/weak-alias injection for cross-file linking
"""

class SourceHarmonizerV757:
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
        self._storage_quals = {
            'static', 'extern', 'inline', 'const', 'volatile', '__attribute__',
            '__restrict', 'restrict', 'register'
        }
        self._ctrl_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
            'break', 'continue', 'case', 'default', 'goto', 'typedef'
        }

    # -------------------------------------------------------------------------
    def setup_workspace(self):
        print(f"[>] Preparing v75.7 Workspace...")
        for folder in [self.target_dir / "src", self.target_dir / "include"]:
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
        for sub in ["src", "include"]:
            src = self.decomp_path / sub
            dst = self.target_dir / sub
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)

    # -------------------------------------------------------------------------
    def remove_strings_and_comments(self, text):
        text = re.sub(r'//[^\n]*', '', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)
        return text

    # -------------------------------------------------------------------------
    def find_static_definitions(self, clean_content):
        """Returns dict {func_name -> signature} for every static function definition."""
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

    # -------------------------------------------------------------------------
    def has_existing_forward_decl(self, clean_content, func_name):
        """
        Returns True only if an actual forward declaration exists for func_name.
        Distinguishes declarations from call statements by requiring:
          (a) a type token before the function name on the same line
          (b) no expression operators (=, !, &, |, etc.) in the prefix
          (c) no open-paren in the prefix (would mean inside an expression)
        """
        pattern = re.compile(
            r'^([ \t]*(?:[^\n]*?))\b' + re.escape(func_name) + r'\s*\([^{}]*?\)\s*;',
            re.MULTILINE
        )
        for m in pattern.finditer(clean_content):
            prefix = m.group(1)
            if re.search(r'[=!&|^~+\-/%<>?]', prefix):
                continue
            if '(' in prefix:
                continue
            tokens = re.findall(r'[a-zA-Z_]\w*', prefix)
            type_tokens = [t for t in tokens
                           if t not in self._storage_quals
                           and t not in self._ctrl_keywords]
            if type_tokens:
                return True
        return False

    # -------------------------------------------------------------------------
    def fix_static_conflicts(self, content):
        """
        Strategy A: patch non-static forward decl -> add `static`.
        Strategy B: inject missing static forward decl (call-before-definition,
                    no existing decl of any kind).
        """
        clean = self.remove_strings_and_comments(content)
        static_defs = self.find_static_definitions(clean)
        if not static_defs:
            return content

        modified = content
        needs_injected = []

        for func_name, sig in static_defs.items():
            # Strategy A
            fwd_pattern = re.compile(
                r'^([ \t]*)(?!static\b)(\b\S[^\n]*?\b'
                + re.escape(func_name) + r'\s*\([^)]*\)\s*;)',
                re.MULTILINE
            )
            patched = fwd_pattern.sub(
                lambda m: f"{m.group(1)}static {m.group(2)}", modified
            )
            if patched != modified:
                modified = patched
                continue

            # Strategy B
            if self.has_existing_forward_decl(clean, func_name):
                continue

            call_pat = re.compile(r'\b' + re.escape(func_name) + r'\s*\(')
            def_pat  = re.compile(
                r'\bstatic\b[^;{}]*?\b' + re.escape(func_name) + r'\s*\([^{}]*?\)\s*\{',
                re.DOTALL
            )
            call_m = call_pat.search(clean)
            def_m  = def_pat.search(clean)
            if call_m and def_m and call_m.start() < def_m.start():
                needs_injected.append(f"static {sig};")

        if needs_injected:
            block = (
                "// --- SH static forward declarations ---\n"
                + "\n".join(needs_injected) + "\n"
                + "// --- SH static forward declarations end ---\n\n"
            )
            last_include = None
            for m in re.finditer(r'^#include\b[^\n]*\n', modified, re.MULTILINE):
                last_include = m
            pos = last_include.end() if last_include else 0
            modified = modified[:pos] + block + modified[pos:]

        return modified

    # -------------------------------------------------------------------------
    def fix_static_local_runtime_init(self, content):
        """
        Fixes static local variables with non-constant (runtime) initializers,
        which Clang rejects under C99 even inside function bodies.

        Form 1 — explicit type present:
          `    static u32 *addr = __codeF0_getLearnedAbilitiesAddress();`
          ->  `    u32 * addr = __codeF0_getLearnedAbilitiesAddress();`
          (strips `static`, leaves as regular local with same type)

        Form 2 — C89 implicit-int (no type, just `static varname = call()`):
          `    static addr = __codeF0_getLearnedAbilitiesAddress();`
          ->  `    addr = __codeF0_getLearnedAbilitiesAddress();`
          (strips `static`, becomes plain assignment to variable declared elsewhere)

        Both forms:
          - Only apply to indented lines (inside function bodies)
          - Only trigger when RHS contains `(...)` (a call, not a constant)
          - Never touch file-scope statics (no leading whitespace)
          - Never touch constant initializers like `static int count = 0;`

        Applied Form 2 BEFORE Form 1 to avoid Form 1 accidentally matching
        implicit-int lines after Form 2 has already converted them.
        """
        # Form 2 first: implicit-int `static varname = call(...);`
        # Requires RHS to contain balanced `(` and `)` (function call)
        form2 = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w+)\s*=\s*([^;\n]+(?:\([^;\n]*\))[^;\n]*)\s*;$',
            re.MULTILINE
        )
        def repl_form2(m):
            indent  = m.group(1)
            varname = m.group(2)
            rhs     = m.group(3).strip()
            return f"{indent}{varname} = {rhs};"

        result = form2.sub(repl_form2, content)

        # Form 1: explicit type `static TYPE *varname = call();`
        # Uses original proven pattern that requires ( in RHS
        form1 = re.compile(
            r'^([ \t]+)(static(?:\s+(?:struct|union|enum))?\s+[^=\n;{}]+?)\b([a-zA-Z_]\w+)\s*=\s*([^;\n]*\([^;\n]*)\s*;$',
            re.MULTILINE
        )
        def repl_form1(m):
            indent    = m.group(1)
            type_part = m.group(2).rstrip()
            varname   = m.group(3)
            rhs       = m.group(4).strip()
            type_only = re.sub(r'\bstatic\b\s*', '', type_part).strip()
            if not type_only:
                type_only = 'int'
            return f"{indent}{type_only} {varname} = {rhs};"

        result = form1.sub(repl_form1, result)
        return result

    # -------------------------------------------------------------------------
    def find_forward_declared_functions(self, clean_content):
        """Returns names of all functions with any forward declaration (excluded from BKA)."""
        names = set()
        pattern = re.compile(r'(?<![;{}])\b([a-zA-Z_]\w*)\s*\([^{}]*?\)\s*;', re.DOTALL)
        for m in pattern.finditer(clean_content):
            name = m.group(1)
            if name in self.c_keywords:
                continue
            prefix = clean_content[:m.start()]
            cut = max(prefix.rfind(';'), prefix.rfind('{'), prefix.rfind('}'))
            segment = prefix[cut+1:] if cut != -1 else prefix
            tokens = set(re.findall(r'[a-zA-Z_]\w*', segment))
            if not tokens or 'typedef' in tokens:
                continue
            names.add(name)
        return names

    # -------------------------------------------------------------------------
    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        # Pass 1 — Array init: `u8 tmp[N] = D_x;` -> __builtin_memcpy
        array_init_pattern = re.compile(
            r'^([ \t]*(?:struct\s+|union\s+|enum\s+)?[a-zA-Z_]\w*(?:\s*\*)*)\s+'
            r'([a-zA-Z_]\w*)\s*\[\s*(\d+)\s*\]\s*=\s*([a-zA-Z_]\w*)\s*;',
            re.MULTILINE
        )
        def array_init_repl(m):
            type_str = m.group(1); name = m.group(2)
            size = m.group(3);     src  = m.group(4)
            return (f"{type_str} {name}[{size}]; "
                    f"__builtin_memcpy({name}, {src}, {size} * sizeof({type_str.strip()}));")

        modified = array_init_pattern.sub(array_init_repl, original_content)

        # Pass 2 — Fix static-follows-non-static declaration conflicts
        modified = self.fix_static_conflicts(modified)

        # Pass 3 — Fix static local variables with runtime initialisers
        modified = self.fix_static_local_runtime_init(modified)

        # Analysis pass
        clean = self.remove_strings_and_comments(modified)

        # Pass 4 — Build BKA exclusion set
        static_func_names  = set(self.find_static_definitions(clean).keys())
        forward_decl_names = self.find_forward_declared_functions(clean)
        excluded_names     = static_func_names | forward_decl_names

        fid = hashlib.md5(str(file_path.name).encode()).hexdigest()[:8]
        func_pattern = re.compile(r'\b([a-zA-Z_]\w*)\s*\([^{;]*\)\s*\{')
        defined_funcs = []

        for match in func_pattern.finditer(clean):
            func_name = match.group(1)
            start_idx = match.start()
            if func_name in self.c_keywords or func_name in self.std_c:
                continue
            if func_name.startswith(self.sdk_prefixes):
                continue
            if func_name.isupper() or func_name.startswith('__'):
                continue
            if func_name in excluded_names:
                continue
            prefix_str = clean[:start_idx]
            cut_idx = max(prefix_str.rfind(';'), prefix_str.rfind('}'), prefix_str.rfind('{'))
            if cut_idx != -1:
                prefix_str = prefix_str[cut_idx+1:]
            tokens = re.findall(r'[a-zA-Z_]\w*', prefix_str)
            if any(k in tokens for k in ['static', 'inline', 'typedef']):
                continue
            defined_funcs.append(func_name)

        defined_funcs = list(dict.fromkeys(defined_funcs))

        # Pass 5 — BKA macro/weak-alias injection
        macros = aliases = ""
        if defined_funcs:
            macros  = "// --- BKA MACROS START ---\n"
            aliases = "\n\n// --- BKA ALIASES START ---\n"
            for func in defined_funcs:
                uname = f"BKA_F_{fid}_{func}"
                macros  += f"#define {func} {uname}\n"
                aliases += f"#undef {func}\n"
                aliases += f"__typeof__({uname}) {func} __attribute__((weak, alias(\"{uname}\")));\n"
            macros  += "// --- BKA MACROS END ---\n\n"
            aliases += "// --- BKA ALIASES END ---\n"

        new_content = macros + modified + aliases

        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            self.stats["changes_made"] += 1

    # -------------------------------------------------------------------------
    def run(self):
        if not self.decomp_path.exists():
            print(f"[!] Error: Decompilation path {self.decomp_path} not found.")
            return
        self.setup_workspace()
        print(f"[*] Applying v75.7 Function-Level Linker Isolation...")
        for file_path in self.target_dir.rglob('*.[ch]'):
            if "include/libc" in str(file_path) or file_path.suffix == '.h':
                continue
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")
        print(f"\n[+] v75.7 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    target = "Android/app/src/main/cpp"
    decomp = "decomp-files"
    SourceHarmonizerV757(target, decomp).run()
