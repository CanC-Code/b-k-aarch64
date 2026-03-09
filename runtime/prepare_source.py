#!/usr/bin/env python3
import re
from pathlib import Path
from itertools import chain

"""
SourceHarmonizer v75.45 — forward decls + return types + GCC array init fixes (expanded)

Changelog v75.45:
- v75.44: fix GCC array init extension in core2/code_41460.c
- New: also fix two instances in core2/code_4A6F0.c (search_start_cube and sp38)
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.45 — Android/NDK compat    */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.45 preamble is ACTIVE"

#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

#include <stddef.h>
#include <stdbool.h>   /* SourceHarmonizer: use native _Bool on Android NDK */

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
/* End compat block v75.45                          */
/* ──────────────────────────────────────────────── */
"""

# ... (all previous functions remain unchanged: count_ifdef_endif, harmonize_string_h, guard_custom_bool_h,
# fix_implicit_bool_decls, fix_return_type_mismatches)

def fix_array_init_extension(file_path: Path, content: str) -> tuple[str, bool]:
    """
    v75.45: Fix GCC extension array init = another_array in multiple core2 files
    Replaces invalid initializers with memcpy calls.
    """
    marker = "/* SourceHarmonizer v75.45: fix array init GCC extension */"
    if marker in content:
        print(f"  [ARRAY_INIT SKIP] Already fixed → {file_path.name}")
        return content, False

    changed = False
    new_content = content

    # Fix 1: code_41460.c (previous)
    if file_path.name == "code_41460.c" and "s32 sp70[3] = D_80366418;" in new_content:
        new_content = new_content.replace(
            "s32 sp70[3] = D_80366418;",
            "s32 sp70[3];\n    memcpy(sp70, D_80366418, sizeof(sp70));"
        )
        changed = True
        print(f"  [ARRAY_INIT FIXED v75.45] code_41460.c sp70 → memcpy")

    # Fix 2: code_4A6F0.c - line ~161
    if file_path.name == "code_4A6F0.c" and "s32 search_start_cube[3] = D_80367504;" in new_content:
        new_content = new_content.replace(
            "s32 search_start_cube[3] = D_80367504;",
            "s32 search_start_cube[3];\n    memcpy(search_start_cube, D_80367504, sizeof(search_start_cube));"
        )
        changed = True
        print(f"  [ARRAY_INIT FIXED v75.45] code_4A6F0.c search_start_cube → memcpy")

    # Fix 3: code_4A6F0.c - line ~538
    if file_path.name == "code_4A6F0.c" and "f32 sp38[3] = D_80367510;" in new_content:
        new_content = new_content.replace(
            "f32 sp38[3] = D_80367510;",
            "f32 sp38[3];\n    memcpy(sp38, D_80367510, sizeof(sp38));"
        )
        changed = True
        print(f"  [ARRAY_INIT FIXED v75.45] code_4A6F0.c sp38 → memcpy")

    if changed:
        return new_content + "\n" + marker + "\n", True

    return content, False


def insert_preamble_and_fixes(file_path: Path) -> bool:
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Cannot read {file_path}: {e}")
        return False

    original = content
    modified = False

    is_c = file_path.suffix == ".c"
    is_cpp = file_path.suffix in {".cpp", ".hpp", ".cc", ".cxx", ".c++"}
    is_header = file_path.suffix == ".h"
    fname_lower = file_path.name.lower()

    if is_c:
        marker = "SourceHarmonizer v75.45 preamble is ACTIVE"
        if marker not in content:
            content = PREAMBLE + "\n" + content
            print(f"  [PREAMBLE+STDBOOL] Inserted in {file_path.name}")
            modified = True

    if is_header and "bool.h" in fname_lower:
        new_content, changed = guard_custom_bool_h(file_path, content)
        if changed:
            content = new_content
            modified = True

    if is_c:
        new_content, changed = fix_implicit_bool_decls(file_path, content)
        if changed:
            content = new_content
            modified = True

        new_content, changed = fix_return_type_mismatches(file_path, content)
        if changed:
            content = new_content
            modified = True

        new_content, changed = fix_array_init_extension(file_path, content)
        if changed:
            content = new_content
            modified = True

    if is_header and "string.h" in fname_lower:
        new_content, changed = harmonize_string_h(file_path, content)
        if changed:
            content = new_content
            modified = True

    if is_cpp:
        content = re.sub(
            r'^\s*#include\s*["<]string\.h[">].*$',
            r'// SourceHarmonizer v75.45: disabled conflicting decomp string.h',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )

        inject = '\n// SourceHarmonizer v75.45: force standard headers\n#include <cstddef>\n#include <cstring>\n#include <stdbool.h>\n\n'
        if "SourceHarmonizer v75.45 preamble" in content:
            content = re.sub(
                r'(/\* End compat block v75\.45.*?\*/\s*)',
                rf'\1{inject}',
                content,
                flags=re.DOTALL | re.IGNORECASE
            )
        else:
            content = inject + content

        print(f"  [C++ SAFETY] Applied in {file_path.name}")
        modified = True

    if content != original:
        try:
            file_path.write_text(content, encoding="utf-8")
            print(f"  [MODIFIED] {file_path.name}")
            return True
        except Exception as e:
            print(f"Write failed {file_path}: {e}")
            return False

    print(f"  [SKIP] {file_path.name}")
    return False


def main():
    dirs = [
        Path("decomp-files/src"),
        Path("decomp-files/include"),
        Path("Android/app/src/main/cpp"),
    ]

    print("SourceHarmonizer v75.45 running – expanded array init fixes")

    count = 0
    for d in dirs:
        if not d.is_dir():
            print(f"  Dir missing: {d}")
            continue
        for p in sorted(chain(d.rglob("*.[ch]"), d.rglob("*.[ch]pp"))):
            if insert_preamble_and_fixes(p):
                count += 1

    print(f"\nFinished. Changed {count} files.")
    print("Recommended:")
    print("  git add decomp-files/src/core2/code_4A6F0.c decomp-files/src/core2/code_41460.c")
    print("  git commit -m 'harmonizer v75.45: fix GCC array initializer extensions in code_4A6F0.c (memcpy)'")
    print("Verify:")
    print("  grep -A 5 'search_start_cube' decomp-files/src/core2/code_4A6F0.c")
    print("  grep -A 5 'sp38' decomp-files/src/core2/code_4A6F0.c")


if __name__ == "__main__":
    main()