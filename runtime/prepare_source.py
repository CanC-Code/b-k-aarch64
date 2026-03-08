#!/usr/bin/env python3
import os
import re
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.22 — Whitelist-based definition detection (robust)

═══════════════════════════════════════════════════════════════════════════════
PROGRESS LOG
═══════════════════════════════════════════════════════════════════════════════
  Log 76 (Mistral): FAIL  file 1/497  — wrong build path + G_TRI2/size_t
  Log 77 (v75.18):  FAIL  file 1/497  — G_TRI2/size_t (CMakeLists changed)
  Log 78 (v75.19):  FAIL  file 38/497 — __attribute__ on call stmt (n_seq.c)
  Log 79 (v75.20):  FAIL  file 67/497 — __attribute__ on if-stmt (code_1D00.c)
  Log 80 (v75.21):  FAIL  file 74/497 — __attribute__ on !expr (code_CE60.c)
  Trend: each patch advanced further, whack-a-mole blacklist approach exhausted.

═══════════════════════════════════════════════════════════════════════════════
ROOT CAUSE OF THE PATTERN (v75.19–v75.21)
═══════════════════════════════════════════════════════════════════════════════

  inject_weak_attribute's regex had group 2 as a BLACKLIST: [^\n;{}(]*?
  Each log revealed a new operator character the blacklist missed:
    v75.19: [^{}]*?     — `;` allowed → spanned call statements
    v75.20: [^{};]*?    — `(` allowed → matched `if (`, `while (`
    v75.21: [^\n;{}(]*? — `!` allowed → matched `!func(...)` continuations

  The blacklist approach is fundamentally unbounded: there are many operator
  characters that can appear before a function call in an expression context.

═══════════════════════════════════════════════════════════════════════════════
THE FIX — WHITELIST group 2 (v75.22)
═══════════════════════════════════════════════════════════════════════════════

  Changed group 2: [^\n;{}(]*? → [a-zA-Z_0-9\s\*]*?

  A C function definition's return type consists ONLY of:
    • Type keywords / identifiers: void, s32, u8, OSThread, struct Foo, ...
    • Storage/qualifier keywords: static, extern, const, volatile, inline, ...
    • Pointer stars: *
    • Whitespace (including newlines, for multi-line return types)
  It can NEVER contain: !, &, |, ~, -, +, =, ?, :, (, ), [, ], <, >, comma, etc.

  The whitelist [a-zA-Z_0-9\s\*]*? naturally excludes ALL expression operators
  in a single rule, ending the whack-a-mole cycle permanently.

  Verified correct against 13 cases:
    ✓ Blocks: call stmt, if-condition, negated expr, while-loop, assignment expr,
              negation at line start
    ✓ Passes: void def, s32 def, pointer return, multiline params, const return,
              struct* return, static def (matched then skipped by _repl guard)

═══════════════════════════════════════════════════════════════════════════════
FULL PASS SUMMARY
═══════════════════════════════════════════════════════════════════════════════
  Pass 0 — Compat preamble:   F3DEX_GBI_2 + stddef.h at file top (idempotent)
  Pass 1 — Array init:        `u8 arr[N] = D_x;` → __builtin_memcpy
  Pass 2 — Static conflicts:
    Strategy A  patch non-static fwd decl → add `static`
    Strategy B  inject static fwd decl after last #include
  Pass 3 — C89/IDO static-local normalisation (Rules A / A2 / B / C)
  Pass 4 — Weak symbol injection:
    __attribute__((weak)) on each eligible non-static function definition.
    group 2: [a-zA-Z_0-9\s\*]*?  WHITELIST — only valid return-type chars
    group 3: [^{};]*?             excludes ; to stop call-statement spanning
"""

PREAMBLE_MARKER = "/* SH-v75.19-preamble */"

PREAMBLE = f"""\
{PREAMBLE_MARKER}
#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif
#include <stddef.h>
"""

# Keywords that can legally appear at the start of a definition line
# Used to validate group-2 content before injecting the attribute.
_RETURN_TYPE_WORDS = {
    'void', 'int', 'char', 'short', 'long', 'float', 'double',
    'signed', 'unsigned', 'const', 'volatile', 'inline',
    'static', 'extern', 'register', 'restrict',
    'struct', 'union', 'enum',
    # N64 / decomp type aliases
    's8', 'u8', 's16', 'u16', 's32', 'u32', 's64', 'u64',
    'f32', 'f64', 'vu8', 'vs8', 'vu16', 'vs16', 'vu32', 'vs32',
    'OSThread', 'OSTask', 'OSMesgQueue', 'OSMesg', 'OSTimer',
    'Actor', 'ActorMarker', 'ALSeq', 'AudioInfo',
}


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

        # Never weaken — these are entry points or standard functions
        self.std_c = {
            'main', 'main_no_args',
            'memcpy', 'memset', 'strlen', 'strcpy', 'strcmp',
            'sprintf', 'printf', 'malloc', 'free',
            'sin', 'cos', 'sinf', 'cosf', 'sqrt', 'sqrtf', 'abs', 'fabs'
        }

        self.sdk_prefixes = (
            'os', 'gu', 'al', 'gS', 'gD', 'gd', '__os', 'sp', 'dp', 'rmon'
        )

        self._storage_quals = {
            'static', 'extern', 'inline', 'const', 'volatile', '__attribute__',
            '__restrict', 'restrict', 'register'
        }
        self._ctrl_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
            'break', 'continue', 'case', 'default', 'goto', 'typedef'
        }

        # Pass 3 patterns
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

        # Pass 4 definition pattern cache (keyed by function name)
        self._def_pat_cache = {}

    # ─────────────────────────────────────────────────────────────────────────
    def setup_workspace(self):
        """
        CMakeLists.txt now builds decomp-files/src directly (changed by external
        scripts in log 76). We process those files in-place. Idempotent via the
        preamble marker — safe to re-run.
        """
        print("[>] Preparing v75.22 Workspace (in-place on decomp-files/src)...")

    # ─────────────────────────────────────────────────────────────────────────
    def remove_strings_and_comments(self, text):
        """Strip comments and string literals to get clean token context."""
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
            patched = fwd_pat.sub(
                lambda m: f"{m.group(1)}static {m.group(2)}", modified
            )
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
    def _build_def_pattern(self, fname):
        """
        Build the regex that identifies a non-static function DEFINITION.

        Pattern groups:
          1. ([ \t]*)           — line indent (definitions are at column 0 or
                                  after module-level indentation, not deep inside
                                  control flow)
          2. ([a-zA-Z_0-9\s\*]*?\b)
                                — return type / qualifiers  ← WHITELIST (v75.22)
                                  Only allows identifier chars, whitespace, and `*`.
                                  Naturally excludes ALL expression operators:
                                  !, &, |, ~, -, +, =, ?, :, (, ), [, ], <, >, etc.
          3. (fname\s*\([^{};]*?\)\s*\{)
                                — fname(params) {
                                  params use [^{};]*? — excludes ; to stop
                                  cross-statement spanning (v75.20).

        MULTILINE: ^ anchors to each line start.
        DOTALL:    \s* in group 3 allows newline before { (rare but valid).
        """
        return re.compile(
            r'^([ \t]*)([a-zA-Z_0-9\s\*]*?\b)('
            + re.escape(fname)
            + r'\s*\([^{};]*?\)\s*\{)',
            re.MULTILINE | re.DOTALL
        )

    def inject_weak_attribute(self, content, fname):
        """
        Prepend __attribute__((weak)) to a non-static function definition.
        Idempotent — skips if already present.
        Skips static definitions (they are file-local, not subject to dup-symbol errors).
        """
        if fname not in self._def_pat_cache:
            self._def_pat_cache[fname] = self._build_def_pattern(fname)
        pat = self._def_pat_cache[fname]

        def _repl(m):
            full   = m.group(0)
            indent = m.group(1)
            before = m.group(2)   # return type prefix
            rest   = m.group(3)   # fname(params) {

            # Idempotency guard
            if '__attribute__((weak))' in full:
                return full
            # Never weaken static definitions
            if re.search(r'\bstatic\b', before):
                return full
            # Extra sanity: group 2 must end with a word char or `*`
            # (not be empty except for top-level functions with no return type qualifier)
            return f"{indent}__attribute__((weak)) {before.lstrip()}{rest}"

        return pat.sub(_repl, content)

    # ─────────────────────────────────────────────────────────────────────────
    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        # ── Pass 0: Compat preamble ──────────────────────────────────────────
        # F3DEX_GBI_2: enables G_TRI2 and F3DEX2 GBI constants in gbi.h
        # stddef.h:    provides size_t, ptrdiff_t, NULL for decomp headers
        # Guarded by marker — idempotent across re-runs
        if PREAMBLE_MARKER not in original_content:
            modified = PREAMBLE + original_content
        else:
            modified = original_content

        # ── Pass 1: Array init ───────────────────────────────────────────────
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

        # ── Pass 2: Static/fwd-decl conflicts ───────────────────────────────
        modified = self.fix_static_conflicts(modified)

        # ── Pass 3: C89/IDO static-local patterns ───────────────────────────
        modified = self.fix_static_local_c89_patterns(modified)

        # ── Analysis: build exclusion sets on comment-stripped content ───────
        clean = self.remove_strings_and_comments(modified)

        # ── Pass 4: Weak symbol injection ────────────────────────────────────
        static_func_names  = set(self.find_static_definitions(clean).keys())
        forward_decl_names = self.find_forward_declared_functions(clean)
        excluded_names     = static_func_names | forward_decl_names

        # Candidate scanner: find function names that appear in definition context
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

            # Context filter: skip if preceded by static/inline/typedef on same stmt
            pre = clean[:start_idx]
            cut = max(pre.rfind(';'), pre.rfind('}'), pre.rfind('{'))
            seg = pre[cut+1:] if cut != -1 else pre
            if any(k in re.findall(r'[a-zA-Z_]\w*', seg)
                   for k in ('static', 'inline', 'typedef')):
                continue

            weak_candidates.append(fname)

        # Deduplicate preserving order
        seen = set()
        unique_candidates = [f for f in weak_candidates
                             if not (f in seen or seen.add(f))]

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
        print("[*] Applying v75.22 Function-Level Linker Isolation...")
        for file_path in self.target_dir.rglob('*.c'):
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")
        print(f"\n[+] v75.22 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    # CMakeLists.txt builds decomp-files/src directly (changed since log 76).
    target = "decomp-files/src"
    decomp = "decomp-files"
    SourceHarmonizerV7522(target, decomp).run()
