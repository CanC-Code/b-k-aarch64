#!/usr/bin/env python3
import re
from pathlib import Path

"""
SourceHarmonizer v75.29 — Android/Clang compatibility & decomp fixes

Changelog v75.29:
- Added automatic fix for 'typedef int bool;' conflict in headers
  → guarded with #ifndef __cplusplus so C++ uses native bool
- Keeps v75.28 static removal + v75.27 array memcpy fix
- Keeps aggressive preamble insertion
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.29 — FORCED Android compat   */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.29 preamble is ACTIVE in this file"

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
/* End forced compat block v75.29                   */
/* ──────────────────────────────────────────────── */
"""

def insert_preamble_and_fixes(file_path: Path):
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Cannot read {file_path}: {e}")
        return False

    original = content

    # 1. Insert/update preamble (force if version changed)
    preamble_marker = "SourceHarmonizer v75.29 preamble is ACTIVE"
    if preamble_marker not in content:
        content = PREAMBLE + content
        print(f"  [PREAMBLE] Inserted/updated in {file_path.name}")

    # 2. Fix array = global_symbol → memcpy
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

    # 3. Remove 'static' from conflicting function definitions
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

    # 4. NEW: Guard 'typedef int bool;' for C++ compatibility
    # Matches common variants: typedef int bool;   or   typedef enum { false, true } bool;
    bool_typedef_pat = re.compile(
        r'(?m)^(\s*)typedef\s+int\s+bool\s*;\s*$'
    )

    def guard_bool_typedef(m):
        indent = m.group(1)
        return (
            f"{indent}#ifndef __cplusplus\n"
            f"{indent}typedef int bool;\n"
            f"{indent}#endif"
        )

    content = bool_typedef_pat.sub(guard_bool_typedef, content)

    # Bonus: also catch enum-style bool if it exists (rare but seen in some decomps)
    enum_bool_pat = re.compile(
        r'(?m)^(\s*)typedef\s+enum\s*\{\s*false\s*=\s*0\s*,\s*true\s*=\s*1\s*\}\s+bool\s*;\s*$'
    )

    def guard_enum_bool(m):
        indent = m.group(1)
        return (
            f"{indent}#ifndef __cplusplus\n"
            f"{indent}typedef enum { false = 0, true = 1 } bool;\n"
            f"{indent}#endif"
        )

    content = enum_bool_pat.sub(guard_enum_bool, content)

    if content != original:
        try:
            file_path.write_text(content, encoding="utf-8")
            print(f"  [MOD] {file_path.name} — fixes applied (array + static + bool guard)")
            return True
        except Exception as e:
            print(f"Cannot write {file_path.name}: {e}")
            return False
    else:
        print(f"  [SKIP] {file_path.name} — no changes")
        return False


def main():
    target_dir = Path("decomp-files")  # Changed to whole decomp-files so it can fix headers too!
    if not target_dir.is_dir():
        print(f"Error: {target_dir} not found")
        return

    print("SourceHarmonizer v75.29 — preamble + array + static + bool guard fixes")
    modified_count = 0

    # Process ALL .c and .h files (headers need the bool fix too)
    for path in sorted(target_dir.rglob("*.[ch]")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    print(f"\nDone. Modified {modified_count} files.")
    print("Commit message suggestion:")
    print("  git commit -m 'harmonizer v75.29: guard typedef bool for C++ compatibility'")
    print("Push and retrigger CI")
    print("Look for:")
    print("  'SourceHarmonizer v75.29 preamble is ACTIVE'")
    print("If new error → paste first compiler error block")


if __name__ == "__main__":
    main()