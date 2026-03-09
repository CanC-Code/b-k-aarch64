#!/usr/bin/env python3
import re
from pathlib import Path

"""
SourceHarmonizer v75.33 — More robust string.h rewrite for Android NDK/Clang

Changelog v75.33:
- Much more flexible regex for detecting string.h body (tries multiple guard patterns)
- Skips rewrite if extern "C" block already exists (avoids double-wrapping)
- Adds #pragma once style guard detection as fallback
- Better comment placement & visibility
- Minor cleanups in other rules
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.33 — FORCED Android/Ndk compat   */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.33 preamble is ACTIVE in this file"

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
/* End forced compat block v75.33                   */
/* ──────────────────────────────────────────────── */
"""

def insert_preamble_and_fixes(file_path: Path) -> bool:
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Cannot read {file_path}: {e}")
        return False

    original = content
    modified = False

    is_cpp = file_path.suffix in {".cpp", ".hpp", ".cxx", ".cc", ".c++"}
    is_header = file_path.suffix == ".h"
    filename_lower = file_path.name.lower()

    # ────────────────────────────────────────────────
    # 1. Insert/update preamble (only .c files)
    # ────────────────────────────────────────────────
    if file_path.suffix == ".c":
        preamble_marker = "SourceHarmonizer v75.33 preamble is ACTIVE"
        if preamble_marker not in content:
            content = PREAMBLE + "\n" + content
            print(f"  [PREAMBLE] Inserted/updated in {file_path.name}")
            modified = True

    # ────────────────────────────────────────────────
    # 2. array = global_symbol  →  memcpy pattern
    # ────────────────────────────────────────────────
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
        indent = m.group(0)[:m.start(1) - m.start(0)]
        return (
            f"{indent}{decl} {name}[{size_expr}];\n"
            f"{indent}__builtin_memcpy({name}, {src}, sizeof({name}));"
        )

    new_content = array_pat.sub(replace_array, content)
    if new_content != content:
        content = new_content
        modified = True
        print(f"  [ARRAY→MEMCPY] Applied in {file_path.name}")

    # ────────────────────────────────────────────────
    # 3. Remove 'static' from function definitions (if conflicting)
    # ────────────────────────────────────────────────
    static_func_pat = re.compile(
        r'(?m)^(\s*)static\s+([a-zA-Z_][\w\s*]*(?:\s*\*+)?)\s+'
        r'([a-zA-Z_]\w*)\s*\(([^)]*)\)\s*\{'
    )

    def remove_static(m):
        indent = m.group(1)
        ret_type = m.group(2)
        name = m.group(3)
        params = m.group(4)
        return f"{indent}{ret_type} {name}({params}) {{"

    new_content = static_func_pat.sub(remove_static, content)
    if new_content != content:
        content = new_content
        modified = True
        print(f"  [STATIC FUNC] Removed static from defs in {file_path.name}")

    # ────────────────────────────────────────────────
    # 4. Guard typedef int bool; in bool.h
    # ────────────────────────────────────────────────
    if "bool.h" in filename_lower:
        bool_pat = re.compile(r'^\s*typedef\s+int\s+bool\s*;\s*$', re.MULTILINE)
        content = bool_pat.sub(
            r'#ifndef __cplusplus\n\0\n#endif',
            content
        )
        print(f"  [BOOL GUARD] Applied in {file_path.name}")
        modified = True

    # ────────────────────────────────────────────────
    # 5. ROBUST string.h rewrite — extern "C" guard
    # ────────────────────────────────────────────────
    if is_header and "string.h" in filename_lower:
        # Skip if already has extern "C" block
        if re.search(r'extern\s*"C"\s*{', content, re.IGNORECASE):
            print(f"  [STRING_H] Already has extern \"C\" — skipping rewrite {file_path.name}")
        else:
            # Try to find common include-guard patterns and wrap the body
            guard_patterns = [
                # Classic #ifndef / #define / #endif style
                r'(#ifndef\s+[^ \n]+\s+#define\s+[^ \n]+\s*)(.*?)(#endif\s*(?:/\*.*?\*/)?\s*$)',
                # #pragma once style + content + possible #endif
                r'(#pragma\s+once\s*)(.*?)(?=\n\s*(?:#endif|/\* End of).*?$|$)',
                # Fallback: everything after first #include or from start
                r'((?:#include\s*["<][^">]+[">]\s*)*)(.*?)(?=\n\s*(?:#endif|/\*).*?$|$)',
            ]

            wrapped = False
            for pat in guard_patterns:
                m = re.search(pat, content, re.DOTALL | re.IGNORECASE | re.MULTILINE)
                if m:
                    before = m.group(1)
                    body = m.group(2).strip()
                    after = content[m.end():].strip()

                    wrap = f"""{before}
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.33 — Wrapped for C++/NDK compat */
/* ──────────────────────────────────────────────── */

#ifdef __cplusplus
extern "C" {{
#endif

{body}

#ifdef __cplusplus
}}
#endif

{after}
"""
                    content = wrap
                    wrapped = True
                    break

            if wrapped:
                print(f"  [STRING_H REWRITE v75.33] Added extern \"C\" guard in {file_path.name}")
                modified = True
            else:
                print(f"  [STRING_H WARN] Could not reliably wrap — manual check needed {file_path.name}")

    # ────────────────────────────────────────────────
    # 6. C++ safety net: force <cstddef> + <cstring> early + disable bad #include <string.h>
    # ────────────────────────────────────────────────
    if is_cpp:
        # Comment out conflicting #include <string.h>
        content = re.sub(
            r'^\s*#include\s*["<]string\.h[">].*$',
            r'// SourceHarmonizer v75.33: disabled conflicting decomp string.h',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )

        # Inject standard headers early (after preamble if present)
        inject = (
            '\n// SourceHarmonizer v75.33: force standard string/memory headers\n'
            '#include <cstddef>\n'
            '#include <cstring>\n\n'
        )

        if "SourceHarmonizer v75.33 preamble is ACTIVE" in content:
            content = re.sub(
                r'(/\* End forced compat block v75\.33.*?\*/\s*)',
                rf'\1{inject}',
                content,
                flags=re.DOTALL | re.IGNORECASE
            )
        else:
            content = inject + content

        print(f"  [C++ SAFETY] Forced <cstddef>/<cstring> in {file_path.name}")
        modified = True

    # ────────────────────────────────────────────────
    # Write if changed
    # ────────────────────────────────────────────────
    if content != original:
        try:
            file_path.write_text(content, encoding="utf-8")
            print(f"  [MODIFIED] {file_path.name}")
            return True
        except Exception as e:
            print(f"Cannot write {file_path}: {e}")
            return False
    else:
        print(f"  [SKIP] {file_path.name} — no changes")
        return False


def main():
    target_dirs = [
        Path("decomp-files/src"),
        Path("decomp-files/include"),
        Path("Android/app/src/main/cpp"),
    ]

    print("SourceHarmonizer v75.33 — robust string.h extern \"C\" + previous fixes")

    modified_count = 0

    for d in target_dirs:
        if not d.is_dir():
            print(f"  Directory not found: {d}")
            continue

        for path in sorted(d.rglob("*.[ch]")) + sorted(d.rglob("*.[ch]pp")):
            if insert_preamble_and_fixes(path):
                modified_count += 1

    print(f"\nDone. Modified {modified_count} files.")
    print("Commit suggestion:")
    print("  git commit -m 'harmonizer v75.33: robust extern \"C\" wrap in decomp string.h'")
    print("After push → retrigger CI")
    print("Quick local verify:")
    print("  grep -A 12 '__cplusplus' decomp-files/include/string.h")
    print("  → should show extern \"C\" { ... } with harmonizer comment")
    print("If still broken → share new build error from first failing .cpp file")


if __name__ == "__main__":
    main()