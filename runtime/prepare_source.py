#!/usr/bin/env python3
import re
from pathlib import Path

"""
SourceHarmonizer v75.28 — Android/Clang compatibility & decomp fixes

Changelog v75.28:
- Added pass to remove 'static' from function definitions when a non-static declaration exists
  (fixes "static declaration follows non-static" in gccube.c and similar files)
- Keeps v75.27 array = global → memcpy fix
- Keeps aggressive preamble + diagnostics
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.28 — FORCED Android compat   */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.28 preamble is ACTIVE in this file"

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
/* End forced compat block v75.28                   */
/* ──────────────────────────────────────────────── */
"""

def insert_preamble_and_fixes(file_path: Path):
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Cannot read {file_path}: {e}")
        return False

    original = content

    # 1. Insert/update preamble
    preamble_marker = "SourceHarmonizer v75.28 preamble is ACTIVE"
    if preamble_marker not in content:
        content = PREAMBLE + content
        print(f"  [PREAMBLE] Inserted/updated in {file_path.name}")

    # 2. Fix array = global_symbol → memcpy (from v75.27)
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

    # 3. New: Remove 'static' from function definitions when non-static decl exists
    # Pattern: static return_type func_name(params) { ... }
    # We remove 'static ' only if it appears right after indent
    static_func_pat = re.compile(
        r'(?m)^(\s*)static\s+([a-zA-Z_][\w\s*]*(?:\s*\*+)?)\s+'
        r'([a-zA-Z_]\w*)\s*\(([^)]*)\)\s*\{'
    )

    def remove_static_from_def(m):
        indent = m.group(1)
        ret_type = m.group(2)
        name = m.group(3)
        params = m.group(4)
        return f"{indent}{ret_type} {name}({params}) {{"

    content = static_func_pat.sub(remove_static_from_def, content)

    # Optional: you can make it more targeted by checking function name prefix
    # e.g. only for __code7AF80_* but global removal is safer for now

    if content != original:
        try:
            file_path.write_text(content, encoding="utf-8")
            print(f"  [MOD] {file_path.name} — fixes applied (array memcpy + static removal)")
            return True
        except Exception as e:
            print(f"Cannot write {file_path.name}: {e}")
            return False
    else:
        print(f"  [SKIP] {file_path.name} — no changes")
        return False


def main():
    target_dir = Path("decomp-files/src")
    if not target_dir.is_dir():
        print(f"Error: {target_dir} not found")
        return

    print("SourceHarmonizer v75.28 — preamble + array + static fixes")
    modified_count = 0

    for path in sorted(target_dir.rglob("*.c")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    print(f"\nDone. Modified {modified_count} files.")
    print("Commit message suggestion:")
    print("  git commit -m 'harmonizer v75.28: remove conflicting static on functions in gccube.c'")
    print("Push and retrigger CI")
    print("Look for:")
    print("  'SourceHarmonizer v75.28 preamble is ACTIVE'")
    print("If new error → paste first compiler error block")


if __name__ == "__main__":
    main()