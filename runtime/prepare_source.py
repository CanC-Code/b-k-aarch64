#!/usr/bin/env python3
import os
import re
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.20 — Fix false-positive weak injection on call statements

═══════════════════════════════════════════════════════════════════════════════
LOG 78 — v75.19 ran (861 files processed, 861 modified). One file failed:
  n_seq.c:133: error: expected identifier or '('
    __attribute__((weak)) n_alSeqEvent(seq, &evt);
                                      ^
═══════════════════════════════════════════════════════════════════════════════

ROOT CAUSE — regex spans across statement boundaries:

  inject_weak_attribute used: fname\s*\([^{}]*?\)\s*\{  (with DOTALL)
  The [^{}]*? group excludes braces but ALLOWS semicolons and newlines.
  In DOTALL mode it will extend across call statements to find the next `{`:

    n_alSeqEvent(seq, &evt);   ← call statement — ends with `;`
    if (evt.type) {            ← `{` found here!

  The regex matches starting at the call `n_alSeqEvent(`, treats `seq, &evt);
  if (evt.type` as the "param list", and considers the `{` of the `if` block
  as the function body opening. This causes __attribute__((weak)) to be
  injected before a call statement instead of a definition — invalid C.

THE FIX — exclude semicolons from the params group:

  Changed [^{}]*? → [^{};]*?

  A function definition's parameter list NEVER contains a `;`.
  A call statement ends with `;`, so [^{};]*? stops there and cannot
  span across statement boundaries. Multi-line definitions still work
  because newlines are still allowed in [^{};]*? (DOTALL still applies).

  Verified: buggy pattern matches `n_alSeqEvent(seq, &evt);\n    if (evt.type) {`
             fixed  pattern matches only `n_alSeqEvent(ALSeq *seq, ALEvent *event) {`

Same fix applied to the definition pattern cache in inject_weak_attribute.

═══════════════════════════════════════════════════════════════════════════════
FULL PASS SUMMARY
═══════════════════════════════════════════════════════════════════════════════
  Pass 0 — Compat preamble:   F3DEX_GBI_2 define + stddef.h (idempotent)
  Pass 1 — Array init:        u8 tmp[N] = D_x;              -> __builtin_memcpy
  Pass 2 — Static conflicts:
    Strategy A                non-static fwd decl            -> add `static`
    Strategy B                missing static fwd decl        -> inject after #includes
  Pass 3 — Static local C89 normalisation (Rules A/A2/B/C):
    Rule A   compound-assign   static LVALUE OP= expr;       -> LVALUE OP= expr;
    Rule A2  member plain-asgn static obj->field = call();   -> obj->field = call();
    Rule B   implicit-int init static v = call();            -> v = call();
    Rule C   typed init        static TYPE v = call();       -> TYPE v = call();
  Pass 4 — Weak symbol injection:
    __attribute__((weak)) on each eligible non-static function definition.
    Definition pattern uses [^{};]*? to prevent spanning across call statements.
"""

PREAMBLE_MARKER = "/* SH-v75.19-preamble */"

PREAMBLE = f"""\
{PREAMBLE_MARKER}
#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif
#include <stddef.h>
"""


class SourceHarmonizerV7520:
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

        self._p3a = re.compile(
            r'^([ \t]+)static\s+([^=\n;{}]+?)\s*([|&^+\-*/%]=|<<=|>>=)',
            re.MULTILINE
        )
        self._p3a2 = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*(?:->|\.)[^=\n;{}]*?)\s*=\s*([^;\n]+?)\s*;[^\n]*$',
            re.MULTILINE
        )
        self._p3b = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*)\s*=\s*'
            r'([^;\n]+(?:\([^;\n]*\))[^;\n]*)\s*;[^\n]*$',
            re.MULTILINE
        )
        self._p3c = re.compile(
            r'^([ \t]+)static\s+([^=\n;{}]+?)\b([a-zA-Z_]\w*)\s*=\s*([^;\n]+)\s*;[^\n]*$',
            re.MULTILINE
        )

        self._def_pat_cache = {}

    # ─────────────────────────────────────────────────────────────────────────
    def setup_workspace(self):
        print("[>] Preparing v75.20 Workspace (in-place on decomp-files/src)...")

    # ─────────────────────────────────────────────────────────────────────────
    def remove_strings_and_comments(self, text):
        text = re.sub(r'//[^\n]*',          '',   text)
        text = re.sub(r'/\*.*?\*/',         '',   text, flags=re.DOTALL)
        text = re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)
        return text

    # ─────────────────────────────────────────────────────────────────────────
    def find_static_definitions(self, clean_content):
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
        clean       = self.remove_strings_and_comments(content)
        static_defs = self.find_static_definitions(clean)
        if not static_defs:
            return content

        modified       = content
        needs_injected = []

        for func_name, sig in static_defs.items():
            fwd_pat = re.compile(
                r'^([ \t]*)(?!static\b)(\b\S[^\n]*?\b'
                + re.escape(func_name) + r'\s*\([^)]*\)\s*;)',
                re.MULTILINE
            )
            patched = fwd_pat.sub(lambda m: f"{m.group(1)}static {m.group(2)}", modified)
            if patched != modified:
                modified = patched
                continue

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
        content = self._p3a.sub(
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} {m.group(3)}",
            content
        )
        content = self._p3a2.sub(
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} = {m.group(3).strip()};",
            content
        )
        content = self._p3b.sub(
            lambda m: f"{m.group(1)}{m.group(2)} = {m.group(3).strip()};",
            content
        )
        def _repl_c(m):
            rhs = m.group(4).strip()
            if '(' not in rhs:
                return m.group(0)
            return f"{m.group(1)}{m.group(2)}{m.group(3)} = {rhs};"
        content = self._p3c.sub(_repl_c, content)
        return content

    # ─────────────────────────────────────────────────────────────────────────
    def find_forward_declared_functions(self, clean_content):
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
    def inject_weak_attribute(self, content, fname):
        """
        Prepend __attribute__((weak)) to a non-static function definition.

        KEY FIX in v75.20: params group uses [^{};]*? (excludes semicolons).
        A function definition's parameter list never contains `;`, so this
        prevents the pattern from spanning across call statements like:
          fname(arg1, arg2);        ← call ends with `;`
          ...
          some_other_func(params) { ← pattern would wrongly match this `{`
        With [^{};]*?, the match stops at the `;` and cannot cross boundaries.
        Multi-line parameters still work since newlines are still allowed.
        """
        if fname not in self._def_pat_cache:
            self._def_pat_cache[fname] = re.compile(
                # group 1: line indent
                # group 2: return type / qualifiers before fname  (no newlines, braces, or semicolons)
                # group 3: fname(params) {   — params exclude {} and ;  (KEY FIX: [^{};]*?)
                r'^([ \t]*)([^\n;{}]*?\b)('
                + re.escape(fname)
                + r'\s*\([^{};]*?\)\s*\{)',
                re.MULTILINE | re.DOTALL
            )
        pat = self._def_pat_cache[fname]

        def _repl(m):
            full   = m.group(0)
            indent = m.group(1)
            before = m.group(2)
            rest   = m.group(3)
            if '__attribute__((weak))' in full:
                return full
            if re.search(r'\bstatic\b', before):
                return full
            return f"{indent}__attribute__((weak)) {before.lstrip()}{rest}"

        return pat.sub(_repl, content)

    # ─────────────────────────────────────────────────────────────────────────
    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        # Pass 0 — Compat preamble (idempotent via marker)
        if PREAMBLE_MARKER not in original_content:
            modified = PREAMBLE + original_content
        else:
            modified = original_content

        # Pass 1 — Array init
        arr_pat = re.compile(
            r'^([ \t]*(?:struct\s+|union\s+|enum\s+)?[a-zA-Z_]\w*(?:\s*\*)*)\s+'
            r'([a-zA-Z_]\w*)\s*\[\s*(\d+)\s*\]\s*=\s*([a-zA-Z_]\w*)\s*;',
            re.MULTILINE
        )
        def _arr_repl(m):
            ts, nm, sz, src = m.group(1), m.group(2), m.group(3), m.group(4)
            return (f"{ts} {nm}[{sz}]; "
                    f"__builtin_memcpy({nm}, {src}, {sz} * sizeof({ts.strip()}));")
        modified = arr_pat.sub(_arr_repl, modified)

        # Pass 2 — Static/forward-decl conflicts
        modified = self.fix_static_conflicts(modified)

        # Pass 3 — C89/IDO static-local patterns
        modified = self.fix_static_local_c89_patterns(modified)

        # Analysis pass
        clean = self.remove_strings_and_comments(modified)

        # Pass 4 — Weak symbol injection
        static_func_names  = set(self.find_static_definitions(clean).keys())
        forward_decl_names = self.find_forward_declared_functions(clean)
        excluded_names     = static_func_names | forward_decl_names

        func_pat = re.compile(r'\b([a-zA-Z_]\w*)\s*\([^{;]*\)\s*\{')

        weak_candidates = []
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

            weak_candidates.append(fname)

        seen = set()
        unique_candidates = []
        for f in weak_candidates:
            if f not in seen:
                seen.add(f)
                unique_candidates.append(f)

        new_content = modified
        for fname in unique_candidates:
            new_content = self.inject_weak_attribute(new_content, fname)

        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            self.stats["changes_made"] += 1

    # ─────────────────────────────────────────────────────────────────────────
    def run(self):
        if not self.target_dir.exists():
            print(f"[!] Error: target directory '{self.target_dir}' not found.")
            return
        self.setup_workspace()
        print("[*] Applying v75.20 Function-Level Linker Isolation...")
        for file_path in self.target_dir.rglob('*.c'):
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")
        print(f"\n[+] v75.20 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    target = "decomp-files/src"
    decomp = "decomp-files"
    SourceHarmonizerV7520(target, decomp).run()
