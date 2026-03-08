#!/usr/bin/env python3
import os
import re
from pathlib import Path

"""
SourceHarmonizer v75.24 → v75.25 patch
Defensive preamble + comprehensive IDO→Clang adaptor for Android NDK

Last failure (log 82 & 83): BOOL macro conflict → parse error in while(..., BOOL(...), ...)
Root cause: Android <stdbool.h> / Objective-C headers sometimes #define BOOL as type
Fix: guarded #define BOOL(x) (!!(x)) inserted reliably at top of every .c file

CHANGELOG snippet:
  Log 82–83:    FAIL  file 271–273/497  — BOOL macro undefined (code_5BEB0.c)
  v75.24–v75.25: Robust preamble replacement + marker version bump
"""

# ──────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

PREAMBLE_MARKER_START = "/* SH-v75.24-preamble */"
PREAMBLE_MARKER_END   = "/* End of SH-v75.24 compatibility preamble */"

PREAMBLE = f"""\
{PREAMBLE_MARKER_START}
/* SourceHarmonizer v75.24 — Android/Clang compatibility preamble */
/* All definitions guarded with #ifndef — safe, never override project headers */

/* F3DEX_GBI_2: enables G_TRI2 and all F3DEX2 GBI opcodes in gbi.h */
#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

/* stddef.h: size_t, ptrdiff_t, NULL — needed by many decomp headers */
#include <stddef.h>

/* BOOL: canonical boolean cast macro (N64 SDK style) */
#ifndef BOOL
#define BOOL(x) (!!(x))
#endif

/* Boolean constants — very common in N64 code */
#ifndef TRUE
#define TRUE  1
#endif
#ifndef FALSE
#define FALSE 0
#endif

/* Arithmetic & range utilities — extremely frequent in game code */
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

{PREAMBLE_MARKER_END}
"""

# Control-flow keywords that can never legally follow `static`
_CTRL_KW_PAT = re.compile(
    r'^([ \t]+)static\s+'
    r'(return|if|else|while|for|do|switch|break|continue|goto|case|default|sizeof)\b',
    re.MULTILINE
)


class SourceHarmonizer:
    def __init__(self, target_dir: str, decomp_path: str):
        self.target_dir  = Path(target_dir).resolve()
        self.decomp_path = Path(decomp_path).resolve()
        self.stats = {"files_processed": 0, "files_modified": 0}

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

        self._def_pat_cache = {}

    def remove_strings_and_comments(self, text: str) -> str:
        text = re.sub(r'//[^\n]*',          '',   text)
        text = re.sub(r'/\*.*?\*/',         '',   text, flags=re.DOTALL)
        text = re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)
        return text

    def find_static_definitions(self, clean_content: str) -> dict:
        static_funcs = {}
        pat = re.compile(
            r'\bstatic\b([^;{}]*?\b([a-zA-Z_]\w*)\s*\([^{}]*?\))\s*\{',
            re.DOTALL
        )
        for m in pat.finditer(clean_content):
            name = m.group(2)
            if name not in self.c_keywords:
                static_funcs[name] = m.group(1).strip()
        return static_funcs

    def has_existing_forward_decl(self, clean_content: str, func_name: str) -> bool:
        pat = re.compile(
            r'^([ \t]*(?:[^\n]*?))\b' + re.escape(func_name) + r'\s*\([^{}]*?\)\s*;',
            re.MULTILINE
        )
        for m in pat.finditer(clean_content):
            prefix = m.group(1)
            if re.search(r'[=!&|^~+\-/%<>?]', prefix) or '(' in prefix:
                continue
            tokens = re.findall(r'[a-zA-Z_]\w*', prefix)
            type_tokens = [t for t in tokens if t not in self._storage_quals and t not in self._ctrl_keywords]
            if type_tokens:
                return True
        return False

    def fix_static_conflicts(self, content: str) -> str:
        clean = self.remove_strings_and_comments(content)
        static_defs = self.find_static_definitions(clean)
        if not static_defs:
            return content

        modified = content
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
            if call_pat.search(clean) and def_pat.search(clean):
                call_m = call_pat.search(clean)
                def_m  = def_pat.search(clean)
                if call_m and def_m and call_m.start() < def_m.start():
                    needs_injected.append(f"static {sig};")

        if needs_injected:
            block = (
                "// --- SH-injected static forward declarations ---\n"
                + "\n".join(needs_injected) + "\n"
                + "// --- end SH static forward declarations ---\n\n"
            )
            last_inc_match = None
            for m in re.finditer(r'^#include\b[^\n]*\n', modified, re.MULTILINE):
                last_inc_match = m
            pos = last_inc_match.end() if last_inc_match else 0
            modified = modified[:pos] + block + modified[pos:]

        return modified

    def fix_static_local_c89_patterns(self, content: str) -> str:
        content = _CTRL_KW_PAT.sub(
            lambda m: f"{m.group(1)}{m.group(2)}", content
        )
        content = self._p3a.sub(
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} {m.group(3)}", content
        )
        content = self._p3a2.sub(
            lambda m: f"{m.group(1)}{m.group(2).rstrip()} = {m.group(3).strip()};",
            content
        )
        content = self._p3b.sub(
            lambda m: f"{m.group(1)}{m.group(2)} = {m.group(3).strip()};", content
        )

        def _rule_c(m):
            rhs = m.group(4).strip()
            if '(' not in rhs:
                return m.group(0)
            indent, type_part, varname = m.group(1), m.group(2), m.group(3)
            return f"{indent}static {type_part}{varname}; {varname} = {rhs};"

        content = self._p3c.sub(_rule_c, content)
        return content

    def find_forward_declared_functions(self, clean_content: str) -> set:
        names = set()
        pat = re.compile(r'(?<![;{}])\b([a-zA-Z_]\w*)\s*\([^{}]*?\)\s*;', re.DOTALL)
        for m in pat.finditer(clean_content):
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

    def _build_def_pattern(self, fname: str):
        return re.compile(
            r'^([ \t]*)([a-zA-Z_0-9\s\*]*?\b)('
            + re.escape(fname)
            + r'\s*\([^{};]*?\)\s*\{)',
            re.MULTILINE | re.DOTALL
        )

    def inject_weak_attribute(self, content: str, fname: str) -> str:
        if fname not in self._def_pat_cache:
            self._def_pat_cache[fname] = self._build_def_pattern(fname)
        pat = self._def_pat_cache[fname]

        def _repl(m):
            full, indent, before, rest = m.group(0), m.group(1), m.group(2), m.group(3)
            if '__attribute__((weak))' in full:
                return full
            if re.search(r'\bstatic\b', before):
                return full
            return f"{indent}__attribute__((weak)) {before.lstrip()}{rest}"

        return pat.sub(_repl, content)

    def ensure_preamble(self, content: str) -> str:
        """Insert or replace the compatibility preamble block."""
        start_marker = PREAMBLE_MARKER_START
        end_marker   = PREAMBLE_MARKER_END

        has_preamble = start_marker in content

        if not has_preamble:
            # Clean insert at top
            return PREAMBLE + content

        # Find and replace existing block
        start_idx = content.find(start_marker)
        if start_idx == -1:
            return PREAMBLE + content  # fallback

        end_idx = content.find(end_marker, start_idx)
        if end_idx == -1:
            # Malformed → just prepend new
            return PREAMBLE + content

        end_idx += len(end_marker)
        # Skip any trailing newline after end marker
        while end_idx < len(content) and content[end_idx].isspace():
            end_idx += 1

        # Replace old block with fresh one
        return content[:start_idx] + PREAMBLE + content[end_idx:]

    def process_file(self, file_path: Path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original = f.read()
        except Exception as e:
            print(f"[!] Cannot read {file_path.name}: {e}")
            return

        modified = self.ensure_preamble(original)

        # Pass 1: array initializers → memcpy
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

        # Pass 2 & 3
        modified = self.fix_static_conflicts(modified)
        modified = self.fix_static_local_c89_patterns(modified)

        # Pass 4: weak symbols
        clean = self.remove_strings_and_comments(modified)
        static_names = set(self.find_static_definitions(clean).keys())
        fwd_names    = self.find_forward_declared_functions(clean)
        excluded     = static_names | fwd_names

        func_pat = re.compile(r'\b([a-zA-Z_]\w*)\s*\([^{;]*\)\s*\{')

        seen = set()
        weak_candidates = []
        for m in func_pat.finditer(clean):
            name = m.group(1)
            start = m.start()

            if (name in self.c_keywords or
                name in self.std_c or
                name.startswith(self.sdk_prefixes) or
                name.isupper() or name.startswith('__') or
                name in excluded):
                continue

            pre = clean[:start]
            cut = max(pre.rfind(';'), pre.rfind('}'), pre.rfind('{'))
            seg = pre[cut+1:] if cut != -1 else pre
            tokens = re.findall(r'[a-zA-Z_]\w*', seg)
            if any(k in tokens for k in ('static', 'inline', 'typedef')):
                continue

            if name not in seen:
                seen.add(name)
                weak_candidates.append(name)

        new_content = modified
        for fname in weak_candidates:
            new_content = self.inject_weak_attribute(new_content, fname)

        if new_content != original:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                self.stats["files_modified"] += 1
                # Optional: print(f"  [MOD] {file_path.name}")
            except Exception as e:
                print(f"[!] Cannot write {file_path.name}: {e}")

        self.stats["files_processed"] += 1

    def run(self):
        if not self.target_dir.is_dir():
            print(f"[!] Directory not found: {self.target_dir}")
            return

        print(f"[*] SourceHarmonizer v75.24 – processing {self.target_dir}")
        print("    Target pattern: **/*.c\n")

        for path in sorted(self.target_dir.rglob("*.c")):
            print(f"  → {path.relative_to(self.target_dir)}")
            self.process_file(path)

        print("\n[+] Finished.")
        print(f"    Files processed : {self.stats['files_processed']}")
        print(f"    Files modified  : {self.stats['files_modified']}")


if __name__ == "__main__":
    harmonizer = SourceHarmonizer(
        target_dir  = "decomp-files/src",
        decomp_path = "decomp-files"
    )
    harmonizer.run()