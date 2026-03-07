#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.6 - Fix has_existing_forward_decl false positive +
                          static local runtime-init splitting

ROOT CAUSES (from log 26):

1. v75.5 REGRESSION — has_existing_forward_decl() false positive in code_F0.c:
   The v75.5 guard used pattern `\bfunc_name\s*\([^{}]*?\)\s*;` which matched
   bare function CALL STATEMENTS (e.g. `__codeF0_areCrcsValid();`) as if they
   were forward declarations. This caused Strategy B to skip injection for
   __codeF0_areCrcsValid and __codeF0_areRomCrcsCorrect, leaving code_F0.c
   unmodified and the static-follows-non-static errors unresolved.

   FIX: has_existing_forward_decl_v4() checks that the line prefix (text before
   the function name) contains a TYPE TOKEN and does NOT contain expression
   operators (=, !, &, |, etc.) or open-parens. This reliably distinguishes:
     DECLARATION: `static bool __codeF0_areCrcsValid();`    -> True  (has `bool`)
     CALL STMT:   `    __codeF0_areCrcsValid();`             -> False (no type token)
     CALL STMT:   `    result = __codeF0_areCrcsValid();`    -> False (has `=`)
     CALL STMT:   `    if(!__codeF0_areCrcsValid()) ...`     -> False (has `!` and `(`)

2. NEW ERRORS in code_F0.c lines 64, 74 — static local with runtime initializer:
   The decomp source contains IDO/C89 patterns like:
     `static u32 *addr = __codeF0_getLearnedAbilitiesAddress();`
   C99 (enforced by Clang) prohibits non-constant initializers for variables
   with static storage duration, even inside function bodies.

   FIX: fix_static_local_runtime_init() (new Pass 3) detects indented static
   variable declarations whose RHS contains a function call (parentheses), and
   splits them into a two-step declaration + assignment:
     `static u32 * addr;`
     `addr = __codeF0_getLearnedAbilitiesAddress();`
   This preserves static-local semantics (persistent across calls) while
   satisfying Clang's constant-initializer requirement.

FULL PASS SUMMARY:
  Pass 1 — Array init:        `u8 tmp[N] = D_x;`  ->  __builtin_memcpy
  Pass 2 — Static conflicts:
    Strategy A: patch non-static forward decl   ->  add `static`
    Strategy B: inject missing static fwd decl  (guarded by improved decl detector)
  Pass 3 — Static local init: `static T v = call();`  ->  `static T v; v = call();`
  Pass 4 — BKA exclusion set: static + forward-declared functions excluded
  Pass 5 — BKA macro/weak-alias injection for cross-file linking
"""

class SourceHarmonizerV756:
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

        # Storage/qualifier keywords that are NOT type names
        self._storage_quals = {
            'static', 'extern', 'inline', 'const', 'volatile', '__attribute__',
            '__restrict', 'restrict', 'register'
        }
        # Control-flow keywords that are NOT type names
        self._ctrl_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
            'break', 'continue', 'case', 'default', 'goto', 'typedef'
        }

    # -------------------------------------------------------------------------
    def setup_workspace(self):
        print(f"[>] Preparing v75.6 Workspace...")
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
        """
        Returns dict { func_name -> signature } for every function defined with
        `static` in this file. Uses re.DOTALL for reliable multiline matching.
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

    # -------------------------------------------------------------------------
    def has_existing_forward_decl(self, clean_content, func_name):
        """
        Returns True ONLY if an actual forward declaration exists for func_name.

        Distinguishes declarations from call statements by requiring that the
        text before the function name on the same line:
          (a) contains at least one TYPE token (not just storage/control keywords)
          (b) does NOT contain expression operators (=, !, &, |, etc.)
          (c) does NOT contain an open-paren (would mean we're inside an expression)

        Examples:
          `static bool foo();`          -> True  (bool is a type token)
          `void foo(Bar *x);`           -> True  (void is a type token)
          `    foo();`                  -> False (no type token in prefix)
          `    result = foo();`         -> False (= operator)
          `    if(!foo()) ...`          -> False (! operator, open-paren)
          `static u32* foo();`          -> True  (u32 is a type token; * allowed)
        """
        pattern = re.compile(
            r'^([ \t]*(?:[^\n]*?))\b' + re.escape(func_name) + r'\s*\([^{}]*?\)\s*;',
            re.MULTILINE
        )
        for m in pattern.finditer(clean_content):
            prefix = m.group(1)
            # Reject if expression operators present (= ! & | ^ ~ + - / % < > ?)
            # Note: * is intentionally excluded — it's valid as a pointer declarator
            if re.search(r'[=!&|^~+\-/%<>?]', prefix):
                continue
            # Reject if inside a sub-expression (open-paren in prefix)
            if '(' in prefix:
                continue
            # Require at least one type-like token (not just storage/control kws)
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
        Two-strategy direct source patch for:
          'static declaration of X follows non-static declaration'

        Strategy A — patch existing explicit non-static forward declaration.
        Strategy B — inject missing static forward declaration ONLY when no
                     forward decl of any kind already exists (using the improved
                     has_existing_forward_decl which correctly ignores call stmts).
        """
        clean = self.remove_strings_and_comments(content)
        static_defs = self.find_static_definitions(clean)
        if not static_defs:
            return content

        modified = content
        needs_injected = []

        for func_name, sig in static_defs.items():
            # Strategy A: patch existing non-static forward decl line
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
                continue

            # Strategy B: inject only when no forward decl of any kind exists
            if self.has_existing_forward_decl(clean, func_name):
                continue

            # Check if function is called before its definition
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
            if last_include:
                pos = last_include.end()
                modified = modified[:pos] + block + modified[pos:]
            else:
                modified = block + modified

        return modified

    # -------------------------------------------------------------------------
    def fix_static_local_runtime_init(self, content):
        """
        Splits static local variables with non-constant (runtime) initializers:
          static u32 *varname = runtime_func(...);
        Into a declaration + deferred assignment:
          static u32 * varname;
          varname = runtime_func(...);

        Required because C99 prohibits non-constant initializers for static-
        storage-duration variables even inside function bodies (Clang error:
        'initializer element is not a compile-time constant').

        Only applies to INDENTED lines (inside function bodies).
        Only triggers when the RHS contains parentheses (a function call/cast).
        Leaves constant initializers like `static int count = 0;` untouched.
        Does not touch file-scope statics (no leading whitespace).
        """
        pattern = re.compile(
            r'^([ \t]+)(static(?:\s+(?:struct|union|enum))?\s+[^=\n;{}]+?)\b([a-zA-Z_]\w+)\s*=\s*([^;\n]*\([^;\n]*)\s*;$',
            re.MULTILINE
        )

        def repl(m):
            indent    = m.group(1)
            type_part = m.group(2).rstrip()  # e.g. `static u32 *`
            varname   = m.group(3)            # e.g. `addr`
            rhs       = m.group(4).strip()    # e.g. `__codeF0_getLearnedAbilitiesAddress()`
            return f"{indent}{type_part} {varname};\n{indent}{varname} = {rhs};"

        return pattern.sub(repl, content)

    # -------------------------------------------------------------------------
    def find_forward_declared_functions(self, clean_content):
        """
        Returns names of all functions with any forward declaration.
        Excluded from BKA to prevent macro/alias interaction.
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
            if not tokens or 'typedef' in tokens:
                continue
            names.add(name)
        return names

    # -------------------------------------------------------------------------
    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        # --- Pass 1: Fix IDO array init  `u8 tmp[N] = D_x;`  ->  __builtin_memcpy ---
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

        # --- Pass 2: Fix static-follows-non-static declaration conflicts ---
        modified_content = self.fix_static_conflicts(modified_content)

        # --- Pass 3: Fix static local variables with runtime initializers ---
        modified_content = self.fix_static_local_runtime_init(modified_content)

        # Analysis on stripped content
        clean_content = self.remove_strings_and_comments(modified_content)

        # --- Pass 4: Build BKA exclusion set ---
        static_func_names  = set(self.find_static_definitions(clean_content).keys())
        forward_decl_names = self.find_forward_declared_functions(clean_content)
        excluded_names     = static_func_names | forward_decl_names

        fid = hashlib.md5(str(file_path.name).encode()).hexdigest()[:8]

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

            prefix_str = clean_content[:start_idx]
            cut_idx = max(prefix_str.rfind(';'), prefix_str.rfind('}'), prefix_str.rfind('{'))
            if cut_idx != -1:
                prefix_str = prefix_str[cut_idx+1:]
            tokens = re.findall(r'[a-zA-Z_]\w*', prefix_str)
            if any(k in tokens for k in ['static', 'inline', 'typedef']):
                continue

            defined_funcs.append(func_name)

        defined_funcs = list(dict.fromkeys(defined_funcs))

        # --- Pass 5: BKA macro/alias injection ---
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

    # -------------------------------------------------------------------------
    def run(self):
        if not self.decomp_path.exists():
            print(f"[!] Error: Decompilation path {self.decomp_path} not found.")
            return

        self.setup_workspace()
        print(f"[*] Applying v75.6 Function-Level Linker Isolation...")

        for file_path in self.target_dir.rglob('*.[ch]'):
            if "include/libc" in str(file_path) or file_path.suffix == '.h':
                continue
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")

        print(f"\n[+] v75.6 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    target = "Android/app/src/main/cpp"
    decomp = "decomp-files"

    harmonizer = SourceHarmonizerV756(target, decomp)
    harmonizer.run()
