#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.8 — Robust C89/IDO-to-Clang Source Normalisation

CHANGE LOG:
  v75.1  Weak-alias BKA strategy; __builtin_memcpy for array init
  v75.2  Static function pre-scan; exclude __ prefix from BKA
  v75.3  fix_static_conflicts Pass 2 (Strategy A+B); forward-decl exclusion set
  v75.4  Direct source patch: static/fwd-decl conflict; two inject strategies
  v75.5  has_existing_forward_decl guard (attacktutorial.c duplicate injection)
  v75.6  Type-aware forward-decl detector (fixes false-positive on bare call stmts);
         Pass 3 Form 1: `static T v = call()` C99 initialiser error
  v75.7  Pass 3 Form 2: C89 implicit-int `static v = call()` (no type token)
  v75.8  Unified Pass 3 — replaces Forms 1/2 with three orthogonal rules covering
         ALL known C89/IDO static-local patterns that Clang C99 rejects:
           Rule A: compound-assign  `static v |= expr`   -> `v |= expr`
           Rule B: implicit-int     `static v = call()`  -> `v = call()`
           Rule C: explicit-type    `static T v = call()` -> `T v = call()`
         Rules are applied in order A→B→C to avoid mutual interference.
         Every rule is gated on indentation (inside function bodies only).
         File-scope statics and constant initialisers are never touched.

ROOT CAUSE (log 28 — castle.c line 383):
  `static unlocked_cheat_flags |= __maCastle_cheatoCodeUnlocked(i);`
  C89/IDO treated `static` as a statement-level storage qualifier that could
  precede any statement. Clang C99 only accepts `static` in declarations, so
  it parses `static unlocked_cheat_flags` as a malformed declaration and
  `|=` as an unexpected token.
  Fix (Rule A): strip `static` from compound-assignment statements.

FULL PASS SUMMARY:
  Pass 1 — Array init         `u8 tmp[N] = D_x;`             -> __builtin_memcpy
  Pass 2 — Static conflicts
    Strategy A                non-static forward decl          -> add `static`
    Strategy B                missing static forward decl      -> inject after #includes
  Pass 3 — Static local C89 normalisation (Rules A/B/C, applied in order)
    Rule A  compound-assign   `static v OP= expr;`            -> `v OP= expr;`
    Rule B  implicit-int init `static v = call();`             -> `v = call();`
    Rule C  typed init        `static TYPE v = call();`        -> `TYPE v = call();`
  Pass 4 — BKA exclusion set  static + forward-declared functions excluded
  Pass 5 — BKA macro/weak-alias injection for cross-file linking
"""


class SourceHarmonizerV758:
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

        # ── Pre-compiled Pass 3 patterns ──────────────────────────────────────
        #
        # Rule A: `    static varname OP= expr;`  ->  `    varname OP= expr;`
        #   Handles compound-assignment C89 idiom. All compound operators covered.
        #   Indentation guard: ^([ \t]+) ensures file-scope statics are untouched.
        self._p3a = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*(?:\s*\[[^\]]*\])?)\s*'
            r'([|&^+\-*/%]=|<<=|>>=)',
            re.MULTILINE
        )

        # Rule B: `    static varname = call(...);`  ->  `    varname = call(...);`
        #   Implicit-int C89 static with runtime initialiser.
        #   Guard: RHS must contain balanced `(...)` — constants are untouched.
        self._p3b = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*)\s*=\s*'
            r'([^;\n]+(?:\([^;\n]*\))[^;\n]*)\s*;$',
            re.MULTILINE
        )

        # Rule C: `    static TYPE *v = call();`  ->  `    TYPE *v = call();`
        #   Explicit-type static with runtime initialiser.
        #   Non-greedy type capture; \w* (not \w+) allows single-char names.
        #   Guard: RHS must contain `(` — applied inside the repl fn.
        self._p3c = re.compile(
            r'^([ \t]+)static\s+([^=\n;{}]+?)\b([a-zA-Z_]\w*)\s*=\s*([^;\n]+)\s*;$',
            re.MULTILINE
        )

    # ─────────────────────────────────────────────────────────────────────────
    def setup_workspace(self):
        print("[>] Preparing v75.8 Workspace...")
        for folder in [self.target_dir / "src", self.target_dir / "include"]:
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
        for sub in ["src", "include"]:
            src = self.decomp_path / sub
            dst = self.target_dir / sub
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)

    # ─────────────────────────────────────────────────────────────────────────
    def remove_strings_and_comments(self, text):
        text = re.sub(r'//[^\n]*',       '',   text)
        text = re.sub(r'/\*.*?\*/',      '',   text, flags=re.DOTALL)
        text = re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)
        return text

    # ─────────────────────────────────────────────────────────────────────────
    def find_static_definitions(self, clean_content):
        """Returns {func_name -> signature} for every static function definition."""
        static_funcs = {}
        pat = re.compile(
            r'\bstatic\b([^;{}]*?\b([a-zA-Z_]\w*)\s*\([^{}]*?\))\s*\{',
            re.DOTALL
        )
        for m in pat.finditer(clean_content):
            name = m.group(2)
            if name not in self.c_keywords and name not in static_funcs:
                static_funcs[name] = m.group(1).strip()
        return static_funcs

    # ─────────────────────────────────────────────────────────────────────────
    def has_existing_forward_decl(self, clean_content, func_name):
        """
        True only if func_name has a real forward declaration (not a call statement).
        Requires a type token in the line prefix, no expression operators, no open-paren.
        This correctly distinguishes:
          `static bool foo();`     -> True   (bool is a type token)
          `    foo();`             -> False  (no type token)
          `    result = foo();`    -> False  (= operator in prefix)
          `    if (!foo()) ...`    -> False  (! operator, open-paren)
        """
        pat = re.compile(
            r'^([ \t]*(?:[^\n]*?))\b' + re.escape(func_name) + r'\s*\([^{}]*?\)\s*;',
            re.MULTILINE
        )
        for m in pat.finditer(clean_content):
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

    # ─────────────────────────────────────────────────────────────────────────
    def fix_static_conflicts(self, content):
        """
        Pass 2: resolve 'static declaration follows non-static declaration'.

        Strategy A — patch existing explicit non-static forward decl:
          `void foo(int x);`  ->  `static void foo(int x);`

        Strategy B — inject missing static forward decl after last #include when:
          • the function is called before its definition, AND
          • no forward declaration of any kind exists (type-aware check).
        """
        clean      = self.remove_strings_and_comments(content)
        static_defs = self.find_static_definitions(clean)
        if not static_defs:
            return content

        modified         = content
        needs_injected   = []

        for func_name, sig in static_defs.items():
            # Strategy A
            fwd_pat = re.compile(
                r'^([ \t]*)(?!static\b)(\b\S[^\n]*?\b'
                + re.escape(func_name) + r'\s*\([^)]*\)\s*;)',
                re.MULTILINE
            )
            patched = fwd_pat.sub(lambda m: f"{m.group(1)}static {m.group(2)}", modified)
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
            last_inc = None
            for m in re.finditer(r'^#include\b[^\n]*\n', modified, re.MULTILINE):
                last_inc = m
            pos      = last_inc.end() if last_inc else 0
            modified = modified[:pos] + block + modified[pos:]

        return modified

    # ─────────────────────────────────────────────────────────────────────────
    def fix_static_local_c89_patterns(self, content):
        """
        Pass 3: fix all three classes of C89/IDO static-local patterns that
        Clang C99 rejects. Applied Rule A → B → C to avoid interference.

        Rule A — compound-assignment (most specific, applied first):
          `    static flags |= call();`    ->  `    flags |= call();`
          Clang parses `static flags` as a malformed declaration; `|=` is a syntax error.
          Strips `static` keyword so the compound assignment is a plain statement.
          Handles all compound operators: |= &= ^= += -= *= /= %= <<= >>=

        Rule B — implicit-int initialiser (applied second):
          `    static varname = call();`   ->  `    varname = call();`
          C89 implicit-int static local with a non-constant initialiser.
          Guard: RHS must contain `(...)` to avoid constant initialisers.

        Rule C — typed initialiser (applied last):
          `    static u32 *ptr = call();`  ->  `    u32 *ptr = call();`
          C99 prohibits non-constant initialisers for static-storage-duration
          variables even inside function bodies (IDO C89 extension).
          Guard: RHS must contain `(` to avoid constant initialisers.

        All rules:
          • Indentation-gated — file-scope statics are never touched
          • Never touch constant initialisers like `static int count = 0;`
          • Never touch static function definitions (handled by Pass 2/BKA)
        """
        # Rule A
        content = self._p3a.sub(
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} {m.group(3)}",
            content
        )

        # Rule B
        content = self._p3b.sub(
            lambda m: f"{m.group(1)}{m.group(2)} = {m.group(3).strip()};",
            content
        )

        # Rule C
        def _repl_c(m):
            rhs = m.group(4).strip()
            if '(' not in rhs:      # constant initialiser — leave alone
                return m.group(0)
            return f"{m.group(1)}{m.group(2)}{m.group(3)} = {rhs};"

        content = self._p3c.sub(_repl_c, content)
        return content

    # ─────────────────────────────────────────────────────────────────────────
    def find_forward_declared_functions(self, clean_content):
        """Returns names of all forward-declared functions (excluded from BKA)."""
        names = set()
        pat   = re.compile(r'(?<![;{}])\b([a-zA-Z_]\w*)\s*\([^{}]*?\)\s*;', re.DOTALL)
        for m in pat.finditer(clean_content):
            name = m.group(1)
            if name in self.c_keywords:
                continue
            prefix  = clean_content[:m.start()]
            cut     = max(prefix.rfind(';'), prefix.rfind('{'), prefix.rfind('}'))
            segment = prefix[cut+1:] if cut != -1 else prefix
            tokens  = set(re.findall(r'[a-zA-Z_]\w*', segment))
            if not tokens or 'typedef' in tokens:
                continue
            names.add(name)
        return names

    # ─────────────────────────────────────────────────────────────────────────
    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        # Pass 1 — Array init: `u8 tmp[N] = D_x;`  ->  __builtin_memcpy
        arr_pat = re.compile(
            r'^([ \t]*(?:struct\s+|union\s+|enum\s+)?[a-zA-Z_]\w*(?:\s*\*)*)\s+'
            r'([a-zA-Z_]\w*)\s*\[\s*(\d+)\s*\]\s*=\s*([a-zA-Z_]\w*)\s*;',
            re.MULTILINE
        )
        def _arr_repl(m):
            ts, nm, sz, src = m.group(1), m.group(2), m.group(3), m.group(4)
            return (f"{ts} {nm}[{sz}]; "
                    f"__builtin_memcpy({nm}, {src}, {sz} * sizeof({ts.strip()}));")

        modified = arr_pat.sub(_arr_repl, original_content)

        # Pass 2 — Fix static/forward-decl conflicts
        modified = self.fix_static_conflicts(modified)

        # Pass 3 — Fix C89/IDO static-local patterns
        modified = self.fix_static_local_c89_patterns(modified)

        # Analysis pass (strip strings/comments for safe scanning)
        clean = self.remove_strings_and_comments(modified)

        # Pass 4 — Build BKA exclusion set
        static_func_names  = set(self.find_static_definitions(clean).keys())
        forward_decl_names = self.find_forward_declared_functions(clean)
        excluded_names     = static_func_names | forward_decl_names

        fid      = hashlib.md5(file_path.name.encode()).hexdigest()[:8]
        func_pat = re.compile(r'\b([a-zA-Z_]\w*)\s*\([^{;]*\)\s*\{')
        defined_funcs = []

        for match in func_pat.finditer(clean):
            fname     = match.group(1)
            start_idx = match.start()
            if fname in self.c_keywords or fname in self.std_c:
                continue
            if fname.startswith(self.sdk_prefixes):
                continue
            if fname.isupper() or fname.startswith('__'):
                continue
            if fname in excluded_names:
                continue
            pre = clean[:start_idx]
            cut = max(pre.rfind(';'), pre.rfind('}'), pre.rfind('{'))
            seg = pre[cut+1:] if cut != -1 else pre
            if any(k in re.findall(r'[a-zA-Z_]\w*', seg)
                   for k in ('static', 'inline', 'typedef')):
                continue
            defined_funcs.append(fname)

        defined_funcs = list(dict.fromkeys(defined_funcs))

        # Pass 5 — BKA macro/weak-alias injection
        macros = aliases = ""
        if defined_funcs:
            macros  = "// --- BKA MACROS START ---\n"
            aliases = "\n\n// --- BKA ALIASES START ---\n"
            for fn in defined_funcs:
                un = f"BKA_F_{fid}_{fn}"
                macros  += f"#define {fn} {un}\n"
                aliases += f"#undef {fn}\n"
                aliases += (f"__typeof__({un}) {fn} "
                            f"__attribute__((weak, alias(\"{un}\")));\n")
            macros  += "// --- BKA MACROS END ---\n\n"
            aliases += "// --- BKA ALIASES END ---\n"

        new_content = macros + modified + aliases

        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            self.stats["changes_made"] += 1

    # ─────────────────────────────────────────────────────────────────────────
    def run(self):
        if not self.decomp_path.exists():
            print(f"[!] Error: decompilation path '{self.decomp_path}' not found.")
            return
        self.setup_workspace()
        print("[*] Applying v75.8 Function-Level Linker Isolation...")
        for file_path in self.target_dir.rglob('*.[ch]'):
            if "include/libc" in str(file_path) or file_path.suffix == '.h':
                continue
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")
        print(f"\n[+] v75.8 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    target = "Android/app/src/main/cpp"
    decomp = "decomp-files"
    SourceHarmonizerV758(target, decomp).run()
