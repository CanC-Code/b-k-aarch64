#!/usr/bin/env python3
import re
from pathlib import Path

"""
SourceHarmonizer v75.31 — Android/Clang compatibility & decomp fixes

Changelog v75.31:
- Targeted rewrite of decomp's include/string.h: wrap declarations in extern "C" + __cplusplus guard
  → fixes the root cause of <cstring> cascade (memcpy/memmove/strncpy/etc. not in global namespace)
  when string.h is indirectly included via ultra64.h / os.h / etc.
- Keeps v75.30 C++ injection as fallback
- Keeps v75.29 bool guard, v75.28 static removal, v75.27 array memcpy fixes
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

    is_cpp = file_path.suffix in {".cpp", ".hpp", ".cxx", ".cc"}

    # 1. Insert/update preamble (only for .c files)
    if file_path.suffix == ".c":
        preamble_marker = "SourceHarmonizer v75.31 preamble is ACTIVE"
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

    # 5. TARGETED FIX: Rewrite decomp's string.h to add extern "C" guard for C++
    if "include/string.h" in str(file_path) or "string.h" in file_path.name.lower():
        # Find the declarations block after #include "structs.h"
        decl_pat = re.compile(
            r'(#include "structs\.h"\s*)(.*?)(#endif\s*$)',
            re.DOTALL | re.IGNORECASE
        )

        def wrap_extern_c(m):
            include_part = m.group(1)
            decls = m.group(2).strip()
            end = m.group(3)
            return f"""{include_part}

#ifdef __cplusplus
extern "C" {{
#endif

{decls}

#ifdef __cplusplus
}}
#endif

{end}"""

        content = decl_pat.sub(wrap_extern_c, content)
        print(f"  [STRING_H REWRITE] Added extern \"C\" + __cplusplus guards in {file_path.name}")

    # 6. Safety net: force <cstddef> + <cstring> in all C++ files
    if is_cpp:
        # Comment out any lingering direct includes of string.h
        content = re.sub(
            r'^\s*#include\s*["<]string\.h[">].*$',
            r'// SourceHarmonizer v75.31: disabled conflicting decomp string.h',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )

        # Inject standards very early
        cstring_inject = (
            '\n// SourceHarmonizer v75.31: force standard headers early\n'
            '#include <cstddef>\n'
            '#include <cstring>\n\n'
        )

        # Insert after preamble if present, else at top
        if "SourceHarmonizer v75.31 preamble is ACTIVE" in content:
            content = re.sub(
                r'(/\* End forced compat block v75\.31.*?\*/\s*)',
                r'\1' + cstring_inject,
                content,
                flags=re.DOTALL
            )
        else:
            content = cstring_inject + content

        print(f"  [C++ SAFETY] Forced <cstddef>/<cstring> in {file_path.name}")

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

    print("SourceHarmonizer v75.31 — preamble + array + static + bool + string.h extern \"C\" fix")

    modified_count = 0

    # Decomp .c
    for path in sorted(target_dir.rglob("*.c")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    # All headers (especially string.h)
    for path in sorted(include_dir.rglob("*.h")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    # Your Android C++ files
    for path in sorted(android_cpp_dir.rglob("*.[ch]pp")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    print(f"\nDone. Modified {modified_count} files.")
    print("Commit suggestion:")
    print("  git commit -m 'harmonizer v75.31: rewrite decomp string.h with extern \"C\" guard for C++ compatibility'")
    print("Push and retrigger CI")
    print("Verify locally:")
    print("  cat decomp-files/include/string.h | grep -A 5 '__cplusplus'")
    print("  → should show extern \"C\" { ... } guarded")
    print("If still fails → paste first .cpp error from new log")


if __name__ == "__main__":
    main()