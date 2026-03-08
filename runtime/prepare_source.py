#!/usr/bin/env python3
import re
from pathlib import Path

"""
SourceHarmonizer v75.30 — Android/Clang compatibility & decomp fixes

Changelog v75.30:
- New C++-only pass: disable conflicting decomp "string.h" and force <cstddef> + <cstring>
  → fixes undeclared memcpy, <cstring> cascade, size_t unknown, sprintf linkage in:
    otr_builder.cpp, exceptasm.cpp, rare_decompression.cpp, resource_mgr.cpp
- Keeps v75.29 bool guard, v75.28 static removal, v75.27 array memcpy fixes
- Preamble only inserted in .c files
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.30 — FORCED Android compat   */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.30 preamble is ACTIVE in this file"

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
/* End forced compat block v75.30                   */
/* ──────────────────────────────────────────────── */
"""

def insert_preamble_and_fixes(file_path: Path):
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Cannot read {file_path}: {e}")
        return False

    original = content

    is_cpp = file_path.suffix in {".cpp", ".hpp", ".cxx", ".cc"}

    # 1. Insert/update preamble (only for .c files)
    if file_path.suffix == ".c":
        preamble_marker = "SourceHarmonizer v75.30 preamble is ACTIVE"
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

    # 3. Remove 'static' from function definitions when conflicting
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

    # 4. Guard 'typedef int bool;' in bool.h
    if "bool.h" in str(file_path):
        bool_typedef_pat = re.compile(
            r'^\s*typedef\s+int\s+bool\s*;\s*$',
            re.MULTILINE
        )

        def guard_bool_typedef(m):
            return '#ifndef __cplusplus\n' + m.group(0) + '\n#endif'

        content = bool_typedef_pat.sub(guard_bool_typedef, content)
        print(f"  [BOOL GUARD] Applied __cplusplus guard in {file_path.name}")

    # 5. NEW: C++-only fix — disable decomp string.h + force standard cstring
    if is_cpp:
        # Comment out any #include "string.h" or <string.h>
        content = re.sub(
            r'^\s*#include\s*["<]string\.h[">]\s*(//.*)?$',
            r'// SourceHarmonizer v75.30: disabled conflicting decomp string.h',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )

        # Inject standard includes right after preamble (or at top)
        cstring_inject = (
            '\n// SourceHarmonizer v75.30: force standard headers for C++\n'
            '#include <cstddef>   // size_t, ptrdiff_t, etc.\n'
            '#include <cstring>   // memcpy, memset, strcpy, etc.\n\n'
        )

        if "SourceHarmonizer v75.30 preamble is ACTIVE" in content:
            # Insert after preamble block
            content = re.sub(
                r'(/\* End forced compat block v75\.30.*?\*/\s*)',
                r'\1' + cstring_inject,
                content,
                flags=re.DOTALL
            )
        else:
            # No preamble → insert at very top
            content = cstring_inject + content

        print(f"  [C++ STRING FIX] Disabled decomp string.h + forced <cstring> in {file_path.name}")

    if content != original:
        try:
            file_path.write_text(content, encoding="utf-8")
            print(f"  [MOD] {file_path.name} — fixes applied")
            return True
        except Exception as e:
            print(f"Cannot write {file_path.name}: {e}")
            return False
    else:
        print(f"  [SKIP] {file_path.name} — no changes")
        return False


def main():
    target_dir = Path("decomp-files/src")
    include_dir = Path("decomp-files/include")
    android_cpp_dir = Path("Android/app/src/main/cpp")  # also scan your custom .cpp files

    print("SourceHarmonizer v75.30 — preamble + array + static + bool guard + C++ string fix")

    modified_count = 0

    # Process .c files in decomp src/
    for path in sorted(target_dir.rglob("*.c")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    # Process all .h in include/
    for path in sorted(include_dir.rglob("*.h")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    # NEW: Also process your custom Android .cpp / .hpp files
    for path in sorted(android_cpp_dir.rglob("*.[ch]pp")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    print(f"\nDone. Modified {modified_count} files.")
    print("Commit suggestion:")
    print("  git commit -m 'harmonizer v75.30: auto-fix string.h conflict in C++ files (memcpy, size_t, etc.)'")
    print("Then push and retrigger CI")
    print("Look for in build log:")
    print("  'SourceHarmonizer v75.30 preamble is ACTIVE'")
    print("  '[C++ STRING FIX] ...' messages for otr_builder.cpp, exceptasm.cpp, etc.")
    print("If still errors → paste the first .cpp compiler error block")


if __name__ == "__main__":
    main()