#!/usr/bin/env python3
import re
from pathlib import Path

"""
SourceHarmonizer v75.27 — Android/Clang compatibility & decomp fixes

Changelog:
- v75.27: Added robust local array = global_symbol → memcpy rewrite
         (fixes "array initializer must be an initializer list" in code_41460.c etc.)
- Keeps aggressive preamble insertion + diagnostics
- Conservative: only rewrites when RHS is a simple identifier (global array name)
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.27 — FORCED Android compat   */
/* This block should appear near top of EVERY .c file */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.27 preamble is ACTIVE in this file"

#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

#include <stddef.h>

#ifdef min
#undef min
#endif
#ifdef max
#undef max
#endif
#ifdef abs
#undef abs
#endif

#ifndef BOOL
#define BOOL(x) (!!(x))
#pragma message "BOOL macro defined by SourceHarmonizer"
#else
#pragma message "BOOL was already defined before SourceHarmonizer"
#endif

#ifndef TRUE
#define TRUE 1
#endif
#ifndef FALSE
#define FALSE 0
#endif

#ifndef ABS
#define ABS(x) ((x) < 0 ? -(x) : (x))
#endif
#ifndef MIN
#define MIN(a,b) ((a) < (b) ? (a) : (b))
#endif
#ifndef MAX
#define MAX(a,b) ((a) > (b) ? (a) : (b))
#endif
#ifndef CLAMP
#define CLAMP(x,lo,hi) ((x) < (lo) ? (lo) : (x) > (hi) ? (hi) : (x))
#endif
#ifndef ARRAY_COUNT
#define ARRAY_COUNT(x) (sizeof(x) / sizeof((x)[0]))
#endif

/* ──────────────────────────────────────────────── */
/* End forced compat block v75.27                   */
/* ──────────────────────────────────────────────── */
"""

def insert_preamble_and_fixes(file_path: Path):
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Cannot read {file_path}: {e}")
        return False

    original = content

    # 1. Insert/update preamble (force replace if version changed)
    preamble_start = "SourceHarmonizer v75.27 preamble is ACTIVE"
    if preamble_start not in content:
        content = PREAMBLE + content
        print(f"  [PREAMBLE] Inserted/updated in {file_path.name}")

    # 2. Fix array = global_symbol → memcpy (the current error pattern)
    # Matches:   type name[size] = GLOBAL_SYM;
    #           (inside function or static)
    array_pat = re.compile(
        r'(?m)^(\s*(?:static\s+)?(?:const\s+)?[a-zA-Z_][\w\s*]*(?:\s*\*+)?)\s+'
        r'([a-zA-Z_]\w*)\s*\[\s*(\d+(?:\s*\*\s*[a-zA-Z_]\w+)?)\s*\]\s*=\s*'
        r'([a-zA-Z_][a-zA-Z0-9_]*)\s*;\s*$'
    )

    def replace_array(m):
        decl = m.group(1).rstrip()
        name = m.group(2)
        size_expr = m.group(3)
        src = m.group(4)
        indent = m.group(0)[:m.group(0).find(m.group(1))]
        return (
            f"{indent}{decl} {name}[{size_expr}];\n"
            f"{indent}__builtin_memcpy({name}, {src}, sizeof({name}));"
        )

    content = array_pat.sub(replace_array, content)

    # Optional: add more patterns here in future (e.g. struct init, designated, etc.)

    if content != original:
        try:
            file_path.write_text(content, encoding="utf-8")
            print(f"  [MOD] {file_path.name} — fixes applied (array memcpy + preamble)")
            return True
        except Exception as e:
            print(f"Cannot write {file_path.name}: {e}")
            return False
    else:
        print(f"  [SKIP] {file_path.name} — no changes needed")
        return False


def main():
    target_dir = Path("decomp-files/src")
    if not target_dir.is_dir():
        print(f"Error: {target_dir} not found")
        return

    print("SourceHarmonizer v75.27 — forcing preamble + array init fixes")
    modified_count = 0

    for path in sorted(target_dir.rglob("*.c")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    print(f"\nDone. Modified {modified_count} files.")
    print("Next step: git add . ; git commit -m 'harmonizer v75.27 - fix array init in code_41460.c'")
    print("Then push and retrigger CI")
    print("Watch for pragma messages in log:")
    print("  'SourceHarmonizer v75.27 preamble is ACTIVE'")
    print("  'BOOL macro defined by SourceHarmonizer'")
    print("If new error appears → paste first compiler error line from log")


if __name__ == "__main__":
    main()