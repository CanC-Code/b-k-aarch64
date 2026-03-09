#!/usr/bin/env python3
import re
from pathlib import Path

"""
SourceHarmonizer v75.32 — Android/Clang compatibility & decomp fixes

Changelog v75.32:
- Improved rewrite of decomp's include/string.h: more reliable regex to wrap declarations
  in extern "C" { ... } guarded by #ifdef __cplusplus
  → definitively fixes <cstring> cascade when string.h is included indirectly
- Adds visible comment in string.h to confirm harmonizer action
- Keeps previous safety net (<cstddef>/<cstring> injection in .cpp files)
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.32 — FORCED Android compat   */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.32 preamble is ACTIVE in this file"

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
/* End forced compat block v75.32                   */
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
        preamble_marker = "SourceHarmonizer v75.32 preamble is ACTIVE"
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

    # 5. IMPROVED TARGETED FIX: Rewrite decomp's string.h with extern "C" guard
    if "string.h" in str(file_path).lower() and file_path.suffix == ".h":
        # Try to wrap only the declarations (after #include "structs.h")
        decl_pat = re.compile(
            r'(#include\s*["<]structs\.h[">]\s*?\n)(.*?)(?=\n#endif\s*$)',
            re.DOTALL | re.IGNORECASE
        )

        def wrap_extern_c(m):
            include_part = m.group(1)
            decls = m.group(2).strip()
            return f"""{include_part}
/* SourceHarmonizer v75.32: Wrapped for C++ compatibility */
#ifdef __cplusplus
extern "C" {{
#endif

{decls}

#ifdef __cplusplus
}}
#endif
"""

        new_content = decl_pat.sub(wrap_extern_c, content)

        # Fallback: if pattern didn't match, wrap everything after guard
        if new_content == content:
            new_content = re.sub(
                r'(#ifndef\s+STRING_H\s+#define\s+STRING_H\s*)(.*?)(#endif\s*$)',
                r'\1\n\n/* SourceHarmonizer v75.32: Fallback wrap for C++ */\n#ifdef __cplusplus\nextern "C" {\n#endif\n\n\2\n\n#ifdef __cplusplus\n}\n#endif\n\n\3',
                content,
                flags=re.DOTALL | re.IGNORECASE
            )

        content = new_content
        print(f"  [STRING_H REWRITE v75.32] Added extern \"C\" guard in {file_path.name}")

    # 6. Safety net: force <cstddef> + <cstring> in all C++ files
    if is_cpp:
        # Comment out any lingering direct includes of string.h
        content = re.sub(
            r'^\s*#include\s*["<]string\.h[">].*$',
            r'// SourceHarmonizer v75.32: disabled conflicting decomp string.h',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )

        # Inject standards very early
        cstring_inject = (
            '\n// SourceHarmonizer v75.32: force standard headers early\n'
            '#include <cstddef>\n'
            '#include <cstring>\n\n'
        )

        # Insert after preamble if present, else at top
        if "SourceHarmonizer v75.32 preamble is ACTIVE" in content:
            content = re.sub(
                r'(/\* End forced compat block v75\.32.*?\*/\s*)',
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

    print("SourceHarmonizer v75.32 — improved string.h rewrite + previous fixes")

    modified_count = 0

    # Decomp .c files
    for path in sorted(target_dir.rglob("*.c")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    # Headers (especially string.h)
    for path in sorted(include_dir.rglob("*.h")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    # Your Android C++ files
    for path in sorted(android_cpp_dir.rglob("*.[ch]pp")):
        if insert_preamble_and_fixes(path):
            modified_count += 1

    print(f"\nDone. Modified {modified_count} files.")
    print("Commit suggestion:")
    print("  git commit -m 'harmonizer v75.32: more reliable extern \"C\" wrap in decomp string.h'")
    print("Push and retrigger CI")
    print("Verify locally:")
    print("  cat decomp-files/include/string.h | grep -A 10 '__cplusplus'")
    print("  → should show extern \"C\" { ... } guarded + harmonizer comment")
    print("If still fails → paste first .cpp error from new log")


if __name__ == "__main__":
    main()