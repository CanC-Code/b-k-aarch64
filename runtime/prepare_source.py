#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.9 — Comprehensive C89/IDO-to-Clang Source Normalisation

CHANGE LOG:
  v75.1  Weak-alias BKA strategy; __builtin_memcpy for array init
  v75.2  Static function pre-scan; exclude __ prefix from BKA
  v75.3  fix_static_conflicts Pass 2 (Strategy A+B); forward-decl exclusion set
  v75.4  Direct source patch: static/fwd-decl conflict; two inject strategies
  v75.5  has_existing_forward_decl guard (attacktutorial.c duplicate injection)
  v75.6  Type-aware forward-decl detector; Pass 3 Form 1: typed static runtime init
  v75.7  Pass 3 Form 2: C89 implicit-int `static v = call()`
  v75.8  Unified Pass 3 Rules A/B/C: compound-assign, implicit-int, explicit-type
  v75.9  Pass 3 expanded:
           Rule A2: struct/member plain assign `static seq->field[i] = call()`
           Rules B/C: allow trailing inline comments after `;` on same line

ROOT CAUSES (log 29 — cseq.c):
  Five errors, two distinct root causes:

  1. Lines 29 + 73 — struct member assignments with `static` prefix:
       `            static seq->evtDeltaTicks[i] = __readVarLen(seq,i);`
       `        static seq->evtDeltaTicks[firstTrack] += __readVarLen(seq,firstTrack);`
     Rule A handled the compound-assign (`+=`) at line 73 (complex lvalue works via
     the greedy [^=\n;{}]+? capture). But line 29's plain `=` was not handled:
       - Rule B requires a SIMPLE identifier LHS (`[a-zA-Z_]\\w*`)
       - Rule C requires type+varname pattern; array subscript `[i]` after member name
         prevents the regex from matching correctly.
     Fix: Rule A2 — detects plain `=` assignment where LHS contains `->` or `.`
     (unambiguously a struct member access, not a type declaration).

  2. Lines 118 + 148 — implicit-int static init with trailing inline comment:
       `    static status = __getTrackByte(seq,track);     /* read the status byte */`
       `            static status = __getTrackByte(seq,track); /* get next two bytes, ignore them */`
     Rule B used `\\s*;$` which requires the semicolon at strict end-of-line.
     With a `/* ... */` comment trailing the `;`, `$` doesn't match after `;`.
     Fix: changed Rule B (and Rule C for consistency) ending to `;[^\\n]*$` to
     allow arbitrary trailing content (comments) after the semicolon.

FULL PASS SUMMARY:
  Pass 1 — Array init          `u8 tmp[N] = D_x;`              -> __builtin_memcpy
  Pass 2 — Static conflicts
    Strategy A                 non-static forward decl           -> add `static`
    Strategy B                 missing static forward decl       -> inject after #includes
  Pass 3 — Static local C89 normalisation (Rules A/A2/B/C, applied in order)
    Rule A   compound-assign   `static LVALUE OP= expr;`         -> `LVALUE OP= expr;`
    Rule A2  member plain-asgn `static obj->field = call();`     -> `obj->field = call();`
    Rule B   implicit-int init `static v = call(); /* cmt */`    -> `v = call();`
    Rule C   typed init        `static TYPE v = call();`          -> `TYPE v = call();`
  Pass 4 — BKA exclusion set   static + forward-declared functions excluded
  Pass 5 — BKA macro/weak-alias injection for cross-file linking
"""


class SourceHarmonizerV759:
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

        # Rule A: compound-assign with ANY lvalue (simple var, struct member, array elem)
        #   `    static LVALUE OP= expr;`  ->  `    LVALUE OP= expr;`
        #   Compound operators: |= &= ^= += -= *= /= %= <<= >>=
        #   The lvalue is captured by non-greedy [^=\n;{}]+? stopping at the operator.
        #   Indentation-gated (^[ \t]+).
        self._p3a = re.compile(
            r'^([ \t]+)static\s+([^=\n;{}]+?)\s*([|&^+\-*/%]=|<<=|>>=)',
            re.MULTILINE
        )

        # Rule A2: plain assign where LHS is a struct/member access (contains -> or .)
        #   `    static seq->field[i] = call();`  ->  `    seq->field[i] = call();`
        #   Distinguishes from declarations: type names never contain `->` or `.member`.
        #   No RHS guard needed — member-access LHS unambiguously marks this as a statement.
        #   Allows trailing inline comments after `;`.
        self._p3a2 = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*(?:->|\.)[^=\n;{}]*?)\s*=\s*([^;\n]+?)\s*;[^\n]*$',
            re.MULTILINE
        )

        # Rule B: implicit-int init with runtime RHS (simple identifier, no type token)
        #   `    static varname = call(); /* comment */`  ->  `    varname = call();`
        #   Guard: RHS must contain balanced `(...)` — constant initialisers untouched.
        #   Trailing comment allowed via `[^\n]*$`.
        self._p3b = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*)\s*=\s*'
            r'([^;\n]+(?:\([^;\n]*\))[^;\n]*)\s*;[^\n]*$',
            re.MULTILINE
        )

        # Rule C: explicit-type init with runtime RHS
        #   `    static u32 *ptr = call();`  ->  `    u32 *ptr = call();`
        #   Guard: RHS must contain `(` — checked in repl fn to allow backtracking.
        #   Uses \w* (not \w+) to allow single-char variable names.
        #   Trailing comment allowed via `[^\n]*$`.
        self._p3c = re.compile(
            r'^([ \t]+)static\s+([^=\n;{}]+?)\b([a-zA-Z_]\w*)\s*=\s*([^;\n]+)\s*;[^\n]*$',
            re.MULTILINE
        )

    # ─────────────────────────────────────────────────────────────────────────
    def setup_workspace(self):
        print("[>] Preparing v75.9 Workspace...")
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
        Requires a type token in the line prefix before the function name,
        no expression operators, and no open-paren (which would indicate an expression).
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

        Strategy A — patch an explicit non-static forward decl to add `static`.
        Strategy B — inject a missing static forward decl after the last #include
                     when a static function is called before its definition and
                     no forward declaration of any kind already exists.
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
        Rules are applied in order A → A2 → B → C to avoid mutual interference.

        Rule A  — compound-assign, any lvalue (most specific, no ambiguity):
          `    static flags |= call();`             ->  `    flags |= call();`
          `    static seq->field[i] += call();`     ->  `    seq->field[i] += call();`
          All compound operators: |= &= ^= += -= *= /= %= <<= >>=
          Lvalue captured by non-greedy [^=\\n;{}]+? which stops at the operator.

        Rule A2 — plain assign with struct/member-access lvalue (unambiguous statement):
          `    static seq->field[i] = call();`      ->  `    seq->field[i] = call();`
          The presence of `->` or `.` in the LHS conclusively identifies this as
          a statement (not a declaration), allowing plain `=` to be safely stripped.
          Trailing inline comments are preserved in the stripped form.

        Rule B  — implicit-int plain assign (runtime RHS, no type token):
          `    static status = call(); /* cmt */`   ->  `    status = call();`
          Guard: RHS must contain balanced `(...)` to avoid touching constants.
          Trailing comment stripped from output (comment is on original source line).

        Rule C  — explicit-type plain assign (runtime RHS, type token present):
          `    static u32 *ptr = call();`            ->  `    u32 *ptr = call();`
          Guard: RHS must contain `(` — checked in replacement function.
          Uses \\w* (not \\w+) to handle single-character variable names.

        All rules:
          • Indentation-gated — file-scope statics are NEVER touched
          • Constant initialisers (e.g. `static int x = 0;`) are NEVER touched
          • Static function definitions (handled by Pass 2/BKA) are NEVER touched
        """
        # Rule A: compound-assign
        content = self._p3a.sub(
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} {m.group(3)}",
            content
        )

        # Rule A2: member-access plain assign
        content = self._p3a2.sub(
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} = {m.group(3).strip()};",
            content
        )

        # Rule B: implicit-int runtime init (with optional trailing comment)
        content = self._p3b.sub(
            lambda m: f"{m.group(1)}{m.group(2)} = {m.group(3).strip()};",
            content
        )

        # Rule C: explicit-type runtime init
        def _repl_c(m):
            rhs = m.group(4).strip()
            if '(' not in rhs:
                return m.group(0)        # constant initialiser — leave alone
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
        print("[*] Applying v75.9 Function-Level Linker Isolation...")
        for file_path in self.target_dir.rglob('*.[ch]'):
            if "include/libc" in str(file_path) or file_path.suffix == '.h':
                continue
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")
        print(f"\n[+] v75.9 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    target = "Android/app/src/main/cpp"
    decomp = "decomp-files"
    SourceHarmonizerV759(target, decomp).run()
