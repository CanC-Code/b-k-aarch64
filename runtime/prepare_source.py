#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.14 — Restore correct architecture; fix v75.13 regressions

═══════════════════════════════════════════════════════════════════════════════
REVIEW OF USER'S v75.13 — FIVE CRITICAL BUGS
═══════════════════════════════════════════════════════════════════════════════

Bug 1 — WRONG SEARCH PATHS (root cause of log 37 linker failure):
  v75.13 searched:
    {GITHUB_WORKSPACE}/src/
    {GITHUB_WORKSPACE}/app/src/main/cpp/
  Actual paths in CI:
    {GITHUB_WORKSPACE}/Android/app/src/main/cpp/src/   (decomp .c files)
    {GITHUB_WORKSPACE}/Android/app/src/main/cpp/include/
  Result: ZERO files processed. Source files never modified.

Bug 2 — MISSING setup_workspace():
  v75.9 copies fresh files from decomp-files/ to the build target on every run.
  v75.13 has no such step. When v75.13 runs and processes zero files, the stale
  .o objects from a PRIOR build (where main_no_args was renamed by an older BKA
  version) remain cached. The linker then cannot find main_no_args because the
  symbol was renamed in the stale .o but the alias was malformed.
  This is exactly the `undefined symbol: main_no_args` error in log 37.

Bug 3 — main_no_args NOT protected:
  v75.13 protected = {'main', 'memcpy', 'memset', 'osViClock'}.
  main_no_args is the game's entry point called from NativeBridge.cpp.
  It must NEVER be renamed or wrapped in BKA aliases.

Bug 4 — GLOBAL RENAME (extremely dangerous):
  v75.13 uses `re.sub(r'\bfn\b', unique_name, content)` to rename ALL
  occurrences of every static function name throughout each file.
  This corrupts: string literals, comments, identifiers that share a name
  substring, and — critically — renames local variables and parameters that
  happen to share a name with a static function in the same file.
  Our v75.9 uses #define macros (scoped to compilation unit) which is safe.

Bug 5 — BROKEN BKA ALIAS PATTERN:
  v75.13 injects `extern __typeof__(BKA_F_x_fn) BKA_F_x_fn;` before seeing
  the definition, then `__typeof__(BKA_F_x_fn) fn __attribute__((weak, alias));`
  after. The extern declaration before the definition is redundant at best,
  and the alias is placed at the END of the file outside any include guard,
  which can trigger "symbol not defined in this translation unit" errors on
  some Clang versions since the renamed symbol may not be visible at that point.

═══════════════════════════════════════════════════════════════════════════════
LOG 37 ANALYSIS — WHAT THE [1/9] BUILD COUNT TELLS US
═══════════════════════════════════════════════════════════════════════════════

The build compiled only [1/9] through [9/9] files — the 9 C++ wrapper files
(NativeBridge.cpp, otr_builder.cpp, etc.). The 870 decomp .c files were ALL
served from the build cache. This means:
  • All 870 .c files compiled successfully in a prior run — C is clean ✓
  • The linker failure is the ONLY remaining issue
  • The undefined symbol comes from a stale .o (built by a prior BKA version
    that renamed main_no_args but failed to export it correctly)

Fix: setup_workspace() copies fresh source files, which changes file content
and forces CMake/ninja to recompile all 870 .c files. With v75.14's correct
BKA exclusion of main_no_args, the symbol will be defined in the .so.

═══════════════════════════════════════════════════════════════════════════════
FULL PASS SUMMARY (unchanged from v75.9)
═══════════════════════════════════════════════════════════════════════════════
  Pass 1 — Array init          u8 tmp[N] = D_x;              -> __builtin_memcpy
  Pass 2 — Static conflicts
    Strategy A                 non-static forward decl        -> add `static`
    Strategy B                 missing static forward decl    -> inject after #includes
  Pass 3 — Static local C89 normalisation (Rules A/A2/B/C)
    Rule A   compound-assign   static LVALUE OP= expr;        -> LVALUE OP= expr;
    Rule A2  member plain-asgn static obj->field = call();    -> obj->field = call();
    Rule B   implicit-int init static v = call(); /* cmt */   -> v = call();
    Rule C   typed init        static TYPE v = call();        -> TYPE v = call();
  Pass 4 — BKA exclusion set   static + forward-declared functions excluded
  Pass 5 — BKA macro/weak-alias injection for cross-file linking
"""


class SourceHarmonizerV7514:
    def __init__(self, target_dir, decomp_path):
        self.target_dir  = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0}

        self.c_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
            'break', 'continue', 'case', 'default', 'goto', 'struct', 'union',
            'enum', 'static', 'extern', 'const', 'volatile', 'inline', 'typedef'
        }

        # Functions that must never be renamed or aliased.
        # main_no_args is the game entry point called directly from NativeBridge.cpp.
        # Renaming it would break the JNI -> game boot call chain.
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

        # ── Pre-compiled Pass 3 patterns ──────────────────────────────────────

        # Rule A: compound-assign, any lvalue (simple var, member access, array elem)
        # `    static LVALUE OP= expr;`  ->  `    LVALUE OP= expr;`
        self._p3a = re.compile(
            r'^([ \t]+)static\s+([^=\n;{}]+?)\s*([|&^+\-*/%]=|<<=|>>=)',
            re.MULTILINE
        )

        # Rule A2: plain assign where LHS contains -> or . (struct/member access)
        # `    static seq->field[i] = call();`  ->  `    seq->field[i] = call();`
        self._p3a2 = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*(?:->|\.)[^=\n;{}]*?)\s*=\s*([^;\n]+?)\s*;[^\n]*$',
            re.MULTILINE
        )

        # Rule B: implicit-int plain assign, runtime RHS, optional trailing comment
        # `    static status = call(); /* cmt */`  ->  `    status = call();`
        # Guard: RHS must contain balanced (...) — constants untouched.
        self._p3b = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*)\s*=\s*'
            r'([^;\n]+(?:\([^;\n]*\))[^;\n]*)\s*;[^\n]*$',
            re.MULTILINE
        )

        # Rule C: explicit-type plain assign, runtime RHS, optional trailing comment
        # `    static u32 *ptr = call();`  ->  `    u32 *ptr = call();`
        # Guard: RHS must contain `(` — checked in repl fn.
        # Uses \w* (not \w+) to handle single-char variable names.
        self._p3c = re.compile(
            r'^([ \t]+)static\s+([^=\n;{}]+?)\b([a-zA-Z_]\w*)\s*=\s*([^;\n]+)\s*;[^\n]*$',
            re.MULTILINE
        )

    # ─────────────────────────────────────────────────────────────────────────
    def setup_workspace(self):
        """
        Copy fresh source files from decomp-files/ to the build target.
        This is critical: it ensures stale .o files from prior builds are
        invalidated (file content changes -> CMake forces recompilation).
        v75.13 omitted this step, causing the stale-cache linker failure.
        """
        print("[>] Preparing v75.14 Workspace...")
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
        text = re.sub(r'//[^\n]*',          '',   text)
        text = re.sub(r'/\*.*?\*/',         '',   text, flags=re.DOTALL)
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
        Strategy A: patch existing non-static forward decl to add `static`.
        Strategy B: inject missing static forward decl after last #include.
        """
        clean       = self.remove_strings_and_comments(content)
        static_defs = self.find_static_definitions(clean)
        if not static_defs:
            return content

        modified       = content
        needs_injected = []

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
        Pass 3: fix all known C89/IDO static-local patterns that Clang C99 rejects.
        Rules applied in order A -> A2 -> B -> C to avoid interference.

        Rule A:  compound-assign any lvalue
                 `static flags |= call();`            -> `flags |= call();`
                 `static seq->field[i] += call();`    -> `seq->field[i] += call();`

        Rule A2: plain assign, struct/member-access lvalue (contains -> or .)
                 `static seq->field[i] = call();`     -> `seq->field[i] = call();`

        Rule B:  implicit-int plain assign (no type token), runtime RHS
                 `static status = call(); /* cmt */`  -> `status = call();`

        Rule C:  explicit-type plain assign, runtime RHS
                 `static u32 *ptr = call();`           -> `u32 *ptr = call();`

        All rules: indentation-gated (no file-scope statics touched),
                   constant initialisers never touched,
                   static function definitions never touched.
        """
        # Rule A
        content = self._p3a.sub(
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} {m.group(3)}",
            content
        )

        # Rule A2
        content = self._p3a2.sub(
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} = {m.group(3).strip()};",
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
            if '(' not in rhs:
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
        # Uses #define (not global regex rename) — scoped to this translation unit.
        # main_no_args and other std_c entries are excluded above; they keep their
        # original symbol names and remain directly linkable from NativeBridge.cpp.
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
        print("[*] Applying v75.14 Function-Level Linker Isolation...")
        for file_path in self.target_dir.rglob('*.[ch]'):
            if "include/libc" in str(file_path) or file_path.suffix == '.h':
                continue
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")
        print(f"\n[+] v75.14 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    target = "Android/app/src/main/cpp"
    decomp = "decomp-files"
    SourceHarmonizerV7514(target, decomp).run()
