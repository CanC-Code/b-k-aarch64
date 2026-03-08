#!/usr/bin/env python3
import re
from pathlib import Path

"""
SourceHarmonizer v75.31 — Android/Clang compatibility & decomp fixes

Changelog v75.31:
- NEW: Special rewrite of decomp's string.h → wraps declarations in extern "C" when __cplusplus
  → fixes the root cause of <cstring> cascade (conflicting strcpy/strcat without memcpy etc.)
- Keeps v75.30 C++ injection as safety net
- Keeps v75.29 bool guard, v75.28 static removal, v75.27 array memcpy
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.31 — FORCED Android compat   */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.31 preamble is ACTIVE in this file"

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
/* End forced compat block v75.31                   */
/* ──────────────────────────────────────────────── */
"""

def insert_preamble_and_fixes(file_path: Path):
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Cannot read {file_path}: {e}")
        return False

    original = content

    is_cpp_file = file_path.suffix in {".cpp", ".hpp", ".cxx", ".cc"}
    is_string_h = "string.h" in str(file_path) and file_path.suffix == ".h"

    # 1. Preamble only for .c files
    if file_path.suffix == ".c":
        preamble_marker = "SourceHarmonizer v75.31 preamble is ACTIVE"
        if preamble_marker not in content:
            content = PREAMBLE + content
            print(f"  [PREAMBLE] Inserted/updated in {file_path.name}")

    # 2. Fix array = global → memcpy
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

    # 3. Remove conflicting 'static' on function definitions
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

    # 4. Guard bool typedef
    if "bool.h" in str(file_path):
        bool_pat = re.compile(r'^\s*typedef\s+int\s+bool\s*;\s*$', re.MULTILINE)
        content = bool_pat.sub(r'#ifndef __cplusplus\n\0\n#endif', content)
        print(f"  [BOOL GUARD] Applied in {file_path.name}")

    # 5. SPECIAL FIX: Rewrite decomp's string.h for C++ compatibility
    if is_string_h:
        # Wrap all declarations after #include "structs.h" in extern "C"
        content = re.sub(
            r'(#include "structs\.h"\s*)(.*)',
            r'\1\n\n#ifdef __cplusplus\nextern "C" {\n#endif\n\n\2\n\n#ifdef __cplusplus\n}\n#endif\n',
            content,
            flags=re.DOTALL
        )
        print(f"  [STRING_H FIX] Wrapped declarations in extern \"C\" + __cplusplus guard")

    # 6. C++ safety net: force <cstddef> and <cstring> early
    if is_cpp_file:
        # Comment out direct #include "string.h" (just in case)
        content = re.sub(
            r'^\s*#include\s*["<]string\.h[">].*$',
            r'// SourceHarmonizer v75.31: disabled conflicting decomp string.h',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )

        # Inject at top (after any preamble)
        inject = (
            '\n// SourceHarmonizer v75.31: force standard C++ string functions\n'
            '#include <cstddef>\n'
            '#include <cstring>\n\n'
        )

        if "SourceHarmonizer v75.31 preamble is ACTIVE" in content:
            content = re.sub(
                r'(/\* End forced compat block v75\.31.*?\*/\s*)',
                r'\1' + inject,
                content,
                flags=re.DOTALL
            )
        else:
            content = inject + content

        print(f"  [C++ STRING SAFETY] Forced <cstddef>/<cstring> in {file_path.name}")

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
    android_cpp_dir = Path("Android/app/src/main/cpp")

    print("SourceHarmonizer v75.31 — full fixes + string.h extern \"C\" guard")

    modified_count = 0

    # Decomp .c files
    for path in sorted(target_dir.rglob("*.c")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    # Include dir (especially string.h!)
    for path in sorted(include_dir.rglob("*.h")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    # Your Android C++ files
    for path in sorted(android_cpp_dir.rglob("*.[ch]pp")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    print(f"\nDone. Modified {modified_count} files.")
    print("Commit suggestion:")
    print("  git commit -m 'harmonizer v75.31: wrap decomp string.h in extern \"C\" for C++ compatibility'")
    print("Then push and retrigger CI")
    print("Verify:")
    print("  cat decomp-files/include/string.h | grep -A 5 'extern \"C\"'")
    print("Should show the guard around declarations.")


if __name__ == "__main__":
    main()