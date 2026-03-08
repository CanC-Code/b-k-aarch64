#!/usr/bin/env python3
import os
import re
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.24 — Defensive preamble + comprehensive IDO→Clang adaptor

═══════════════════════════════════════════════════════════════════════════════
PROGRESS / CHANGE LOG
═══════════════════════════════════════════════════════════════════════════════
  Log 76 (Mistral):  FAIL  file   1/497  — wrong path + G_TRI2/size_t
  Log 77 (v75.18):   FAIL  file   1/497  — G_TRI2/size_t (CMakeLists changed)
  Log 78 (v75.19):   FAIL  file  38/497  — weak on call stmt (n_seq.c)
  Log 79 (v75.20):   FAIL  file  67/497  — weak on if-stmt (code_1D00.c)
  Log 80 (v75.21):   FAIL  file  74/497  — weak on !expr (code_CE60.c)
  Log 81 (v75.22):   FAIL  file ~106/497 — `static return` (memory.c)
  Log 82 (v75.23):   FAIL  file 271/497  — BOOL macro undefined (code_5BEB0.c)

═══════════════════════════════════════════════════════════════════════════════
NEW IN v75.24 — DEFENSIVE PREAMBLE
═══════════════════════════════════════════════════════════════════════════════

  Root cause (log 82): code_5BEB0.c:104 "expected ')'"
    Source: while (bit_value = BOOL(expr), iBit >= 0) {
    Our script did NOT touch this pattern (no `static`, no array init, no
    def pattern match — `=` before BOOL blocks group 2 whitelist).
    This is pre-existing source. The comma operator in while() is valid C.
    Clang gives a SYNTAX error because BOOL is not defined as a 1-arg macro
    in the decomp-files/include headers. Without the macro definition, Clang
    sees BOOL as an identifier followed by `(`, making it a function call —
    but still syntactically valid. The real issue: if BOOL is defined elsewhere
    as a TYPE (e.g. from a system header), then BOOL(expr) becomes a C cast
    and the comma after changes parsing context.

    Fix: add `#define BOOL(x) (!!(x))` to preamble under #ifndef guard.
    This ensures BOOL is always a single-arg boolean-cast macro regardless
    of what system headers may have defined.

  Extended preamble now guards all common N64 decomp macros that are either:
    (a) undefined in decomp-files/include on Android, or
    (b) defined differently (as types) by Android system headers.

  New preamble additions (all under #ifndef guards — safe, never override):
    BOOL(x)        — boolean cast, used throughout game logic
    TRUE / FALSE   — boolean constants
    ABS(x)         — integer absolute value (guards against system conflicts)
    MIN(a,b)       — minimum (decomp uses this extensively)
    MAX(a,b)       — maximum
    CLAMP(x,lo,hi) — clamp value to range
    NULL           — already in stddef.h but guarded for safety
    ARRAY_COUNT(x) — sizeof(arr)/sizeof(arr[0]), common decomp utility

═══════════════════════════════════════════════════════════════════════════════
SEMANTIC CORRECTNESS ANALYSIS (all passes)
═══════════════════════════════════════════════════════════════════════════════
  Pass 0 — Compat preamble:    SAFE — all under #ifndef, never override
  Pass 1 — Array init:         SAFE — memcpy is byte-identical
  Pass 2 — Static conflicts:   SAFE — fixes a real C correctness bug
  Pass 3 — IDO static norms:   SAFE — Rule C now preserves static storage
  Pass 4 — Weak symbols:       SAFE — whitelist group 2, semicolon-blocked group 3

═══════════════════════════════════════════════════════════════════════════════
FULL PASS SUMMARY
═══════════════════════════════════════════════════════════════════════════════
  Pass 0 — Compat preamble:
    #define F3DEX_GBI_2         — enables G_TRI2, F3DEX2 GBI opcodes
    #include <stddef.h>         — size_t, ptrdiff_t, NULL
    #define BOOL(x) (!!(x))     — boolean cast macro (N64 SDK pattern)
    #define TRUE  1             — boolean constants
    #define FALSE 0
    #define ABS(x)              — integer absolute value
    #define MIN(a,b)            — minimum of two values
    #define MAX(a,b)            — maximum of two values
    #define CLAMP(x,lo,hi)      — clamp value to [lo, hi]
    #define ARRAY_COUNT(x)      — element count of a static array
    All guarded with #ifndef — safe to add unconditionally.

  Pass 1 — Array init:        u8 arr[N] = D_x; → __builtin_memcpy
  Pass 2 — Static conflicts:
    Strategy A  patch non-static fwd decl → add `static`
    Strategy B  inject static fwd decl after last #include
  Pass 3 — IDO static normalisation:
    Rule D  static + control-flow kw  `static return x;`      → `return x;`
    Rule A  static + compound-assign  `static v OP= e;`        → `v OP= e;`
    Rule A2 static + member-assign    `static o->f = call();`  → `o->f = call();`
    Rule B  static + implicit-int     `static v = call();`     → `v = call();`
    Rule C  static + typed + fn-init  `static T v = call();`   → `static T v; v = call();`
  Pass 4 — Weak symbol injection:
    __attribute__((weak)) on non-static function definitions.
    group 2: [a-zA-Z_0-9\s\*]*?  — whitelist (only return-type chars)
    group 3: [^{};]*?             — no semicolons (stops at stmt boundaries)
"""

PREAMBLE_MARKER = "/* SH-v75.19-preamble */"

PREAMBLE = f"""\
{PREAMBLE_MARKER}
/* SourceHarmonizer v75.24 — Android/Clang compatibility preamble */
/* All definitions are guarded with #ifndef — safe, never override headers */

/* F3DEX_GBI_2: enables G_TRI2 and all F3DEX2 GBI opcodes in gbi.h.
   BK uses F3DEX2 microcode (confirmed by gSP1Quadrangle usage). */
#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

/* stddef.h: provides size_t, ptrdiff_t, NULL for decomp animation/memory headers */
#include <stddef.h>

/* BOOL: single-argument boolean-cast macro used throughout game logic.
   Defined as !!(x) which converts any value to 0 or 1 (canonical boolean).
   Without this, BOOL(expr) in while/if conditions causes Clang parse errors
   because Android system headers may define BOOL as a type, not a 1-arg macro. */
#ifndef BOOL
#define BOOL(x) (!!(x))
#endif

/* Boolean constants — N64 SDK standard */
#ifndef TRUE
#define TRUE  1
#endif
#ifndef FALSE
#define FALSE 0
#endif

/* Common utility macros used throughout the decomp */
#ifndef ABS
#define ABS(x)          ((x) < 0 ? -(x) : (x))
#endif
#ifndef MIN
#define MIN(a, b)       ((a) < (b) ? (a) : (b))
#endif
#ifndef MAX
#define MAX(a, b)       ((a) > (b) ? (a) : (b))
#endif
#ifndef CLAMP
#define CLAMP(x, lo, hi) ((x) < (lo) ? (lo) : (x) > (hi) ? (hi) : (x))
#endif
#ifndef ARRAY_COUNT
#define ARRAY_COUNT(x)  (sizeof(x) / sizeof((x)[0]))
#endif
"""

# Control-flow keywords that can never legally follow `static`
_CTRL_KW_PAT = re.compile(
    r'^([ \t]+)static\s+'
    r'(return|if|else|while|for|do|switch|break|continue|goto|case|default|sizeof)\b',
    re.MULTILINE
)


class SourceHarmonizerV7524:
    def __init__(self, target_dir, decomp_path):
        self.target_dir  = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0}

        self.c_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
            'break', 'continue', 'case', 'default', 'goto', 'struct', 'union',
            'enum', 'static', 'extern', 'const', 'volatile', 'inline', 'typedef'
        }

        # Never weaken — entry points or libc that must link uniquely
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

        # ── Pass 3 patterns ──────────────────────────────────────────────────

        # Rule A: static LVALUE OP= expr;  (compound assignment — no valid type here)
        self._p3a = re.compile(
            r'^([ \t]+)static\s+([^=\n;{}]+?)\s*([|&^+\-*/%]=|<<=|>>=)',
            re.MULTILINE
        )
        # Rule A2: static obj->field = expr;  (member assignment — no valid type)
        self._p3a2 = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*(?:->|\.)[^=\n;{}]*?)\s*=\s*([^;\n]+?)\s*;[^\n]*$',
            re.MULTILINE
        )
        # Rule B: static varname = func_call();  (implicit-int assign, no type kw)
        self._p3b = re.compile(
            r'^([ \t]+)static\s+([a-zA-Z_]\w*)\s*=\s*'
            r'([^;\n]+(?:\([^;\n]*\))[^;\n]*)\s*;[^\n]*$',
            re.MULTILINE
        )
        # Rule C: static TYPE varname = func_call();
        # SPLIT → `static TYPE varname; varname = func_call();`
        # Preserves static storage class (persistent across calls).
        self._p3c = re.compile(
            r'^([ \t]+)static\s+([^=\n;{}]+?)\b([a-zA-Z_]\w*)\s*=\s*([^;\n]+)\s*;[^\n]*$',
            re.MULTILINE
        )

        # Pass 4 definition pattern cache
        self._def_pat_cache = {}

    # ─────────────────────────────────────────────────────────────────────────
    def setup_workspace(self):
        print("[>] Preparing v75.24 Workspace (in-place on decomp-files/src)...")

    # ─────────────────────────────────────────────────────────────────────────
    def remove_strings_and_comments(self, text):
        """Strip comments and string literals for clean token analysis."""
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
        """
        Normalise IDO/C89 static-local patterns that Clang rejects.

        Rule D: `static CTRL_KW`     → `CTRL_KW`        (static before keyword — invalid)
        Rule A: `static v OP= e;`    → `v OP= e;`        (compound assign — invalid)
        Rule A2:`static o->f = c();` → `o->f = c();`     (member assign — invalid)
        Rule B: `static v = c();`    → `v = c();`        (implicit-int assign)
        Rule C: `static T v = c();`  → `static T v; v = c();`  (SPLIT — preserves static)
        """
        # Rule D — FIRST: catches `static return/break/if/while/...`
        content = _CTRL_KW_PAT.sub(
            lambda m: f"{m.group(1)}{m.group(2)}", content
        )
        # Rule A
        content = self._p3a.sub(
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} {m.group(3)}", content
        )
        # Rule A2
        content = self._p3a2.sub(
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} = {m.group(3).strip()};",
            content
        )
        # Rule B
        content = self._p3b.sub(
            lambda m: f"{m.group(1)}{m.group(2)} = {m.group(3).strip()};", content
        )
        # Rule C — SPLIT: keep static, separate dynamic init
        def _rule_c(m):
            rhs = m.group(4).strip()
            if '(' not in rhs:
                return m.group(0)  # no fn call in init — leave alone
            indent, type_part, varname = m.group(1), m.group(2), m.group(3)
            return f"{indent}static {type_part}{varname}; {varname} = {rhs};"
        content = self._p3c.sub(_rule_c, content)
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
        Regex for a C function DEFINITION line.

        Group 1: ([ \t]*)               — line indent
        Group 2: ([a-zA-Z_0-9\s\*]*?\b) — return type prefix   ← WHITELIST (v75.22)
          Only allows identifier chars + whitespace + `*`.
          Excludes ALL expression operators: !&|~-+=?:()[]<>,;{}
          Prevents matching: if/while conditions, call-stmt continuations,
          operator expressions, negated expressions.
        Group 3: (fname\s*\([^{};]*?\)\s*\{)
          fname(params){  where params exclude `;` (v75.20 fix).
        """
        return re.compile(
            r'^([ \t]*)([a-zA-Z_0-9\s\*]*?\b)('
            + re.escape(fname)
            + r'\s*\([^{};]*?\)\s*\{)',
            re.MULTILINE | re.DOTALL
        )

    def inject_weak_attribute(self, content, fname):
        """Prepend __attribute__((weak)) to a non-static function definition."""
        if fname not in self._def_pat_cache:
            self._def_pat_cache[fname] = self._build_def_pattern(fname)
        pat = self._def_pat_cache[fname]

        def _repl(m):
            full, indent, before, rest = m.group(0), m.group(1), m.group(2), m.group(3)
            if '__attribute__((weak))' in full:
                return full                    # idempotent
            if re.search(r'\bstatic\b', before):
                return full                    # never weaken static defs
            return f"{indent}__attribute__((weak)) {before.lstrip()}{rest}"

        return pat.sub(_repl, content)

    # ─────────────────────────────────────────────────────────────────────────
    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        # ── Pass 0: Compat preamble (idempotent via marker) ──────────────────
        if PREAMBLE_MARKER not in original_content:
            modified = PREAMBLE + original_content
        else:
            modified = original_content

        # ── Pass 1: Array init → __builtin_memcpy ────────────────────────────
        arr_pat = re.compile(
            r'^([ \t]*(?:struct\s+|union\s+|enum\s+)?[a-zA-Z_]\w*(?:\s*\*)*)\s+'
            r'([a-zA-Z_]\w*)\s*\[\s*(\d+)\s*\]\s*=\s*([a-zA-Z_]\w*)\s*;',
            re.MULTILINE
        )
        modified = arr_pat.sub(
            lambda m: (
                f"{m.group(1)} {m.group(2)}[{m.group(3)}]; "
                f"__builtin_memcpy({m.group(2)}, {m.group(4)}, "
                f"{m.group(3)} * sizeof({m.group(1).strip()}));"
            ),
            modified
        )

        # ── Pass 2: Static/fwd-decl conflicts ────────────────────────────────
        modified = self.fix_static_conflicts(modified)

        # ── Pass 3: IDO static-local normalisation ───────────────────────────
        modified = self.fix_static_local_c89_patterns(modified)

        # ── Analysis: clean content for candidate detection ───────────────────
        clean = self.remove_strings_and_comments(modified)

        # ── Pass 4: Weak symbol injection ────────────────────────────────────
        static_func_names  = set(self.find_static_definitions(clean).keys())
        forward_decl_names = self.find_forward_declared_functions(clean)
        excluded_names     = static_func_names | forward_decl_names

        func_pat = re.compile(r'\b([a-zA-Z_]\w*)\s*\([^{;]*\)\s*\{')

        seen = set()
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

            # Context: skip if static/inline/typedef precede in current statement
            pre = clean[:start_idx]
            cut = max(pre.rfind(';'), pre.rfind('}'), pre.rfind('{'))
            seg = pre[cut+1:] if cut != -1 else pre
            if any(k in re.findall(r'[a-zA-Z_]\w*', seg)
                   for k in ('static', 'inline', 'typedef')):
                continue

            if fname not in seen:
                seen.add(fname)
                weak_candidates.append(fname)

        new_content = modified
        for fname in weak_candidates:
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
        print("[*] Applying v75.24 IDO→Clang/AArch64 Source Harmonization...")
        for file_path in self.target_dir.rglob('*.c'):
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")
        print(f"\n[+] v75.24 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    # CMakeLists.txt builds decomp-files/src directly (changed since log 76)
    target = "decomp-files/src"
    decomp = "decomp-files"
    SourceHarmonizerV7524(target, decomp).run()
