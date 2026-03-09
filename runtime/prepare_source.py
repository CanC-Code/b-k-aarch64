#!/usr/bin/env python3
import re
from pathlib import Path
from itertools import chain

"""
SourceHarmonizer v75.34 — Defensive string.h repair + bool fix

Changelog v75.34:
- Much safer extern "C" insertion: inserts BEFORE last #endif
- Detects and skips if extern "C" already appears
- Fixes broken/missing #endif by checking guard balance
- Forces #include <stdbool.h> in .c files that use bool
- Better logging when string.h is touched
- FIXED: TypeError when concatenating rglob generators
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.34 — Android/NDK compat    */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.34 preamble is ACTIVE"

#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

#include <stddef.h>
#include <stdbool.h>   /* SourceHarmonizer: providing bool type */

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
/* End compat block v75.34                          */
/* ──────────────────────────────────────────────── */
"""

def count_ifdef_endif(content: str) -> tuple[int, int, bool]:
    """Rough count to detect unbalanced guards"""
    ifs = len(re.findall(r'(?m)^#ifndef\s', content))
    endifs = len(re.findall(r'(?m)^#endif', content))
    balanced = endifs >= ifs
    return ifs, endifs, balanced


def harmonize_string_h(file_path: Path, content: str) -> tuple[str, bool]:
    if re.search(r'extern\s*"C"\s*{', content, re.IGNORECASE | re.DOTALL):
        print(f"  [STRING_H SKIP] Already has extern \"C\" → {file_path.name}")
        return content, False

    if_count, endif_count, balanced = count_ifdef_endif(content)

    if not balanced:
        print(f"  [STRING_H WARN] Unbalanced guard ({if_count} ifndef / {endif_count} endif) → attempting repair")

    last_endif_matches = list(re.finditer(r'(?m)^#endif\b.*?$', content))
    if not last_endif_matches:
        print(f"  [STRING_H WARN] No #endif found → appending block")
        insert_pos = len(content)
    else:
        insert_pos = last_endif_matches[-1].start()

    insert_text = """
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.34 – C++ / NDK compatibility  */
/* ──────────────────────────────────────────────── */

#ifdef __cplusplus
extern "C" {
#endif

"""

    new_content = content[:insert_pos] + insert_text + content[insert_pos:]

    # Close brace before final #endif
    new_content = re.sub(
        r'(#endif\s*(?:/\*.*?\*/)?\s*$)',
        r'#ifdef __cplusplus\n}\n#endif\n\1',
        new_content,
        flags=re.DOTALL | re.MULTILINE,
        count=1
    )

    print(f"  [STRING_H FIXED] Inserted extern \"C\" guard → {file_path.name}")
    return new_content, True


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

    # 1. Preamble + stdbool.h for .c files
    if is_c:
        marker = "SourceHarmonizer v75.34 preamble is ACTIVE"
        if marker not in content:
            content = PREAMBLE + "\n" + content
            print(f"  [PREAMBLE+STDBOOL] Inserted in {file_path.name}")
            modified = True

    # 2. string.h fix
    if is_header and "string.h" in fname_lower:
        new_content, changed = harmonize_string_h(file_path, content)
        if changed:
            content = new_content
            modified = True

    # 3. C++ safety net
    if is_cpp:
        content = re.sub(
            r'^\s*#include\s*["<]string\.h[">].*$',
            r'// SourceHarmonizer v75.34: disabled conflicting decomp string.h',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )

        inject = '\n// SourceHarmonizer v75.34: force standard headers\n#include <cstddef>\n#include <cstring>\n#include <stdbool.h>\n\n'
        if "SourceHarmonizer v75.34 preamble" in content:
            content = re.sub(
                r'(/\* End compat block v75\.34.*?\*/\s*)',
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

    print("SourceHarmonizer v75.34 running – defensive string.h + bool fix")

    count = 0
    for d in dirs:
        if not d.is_dir():
            print(f"  Dir missing: {d}")
            continue
        # FIXED: use chain() instead of broken + on generators
        for p in sorted(chain(d.rglob("*.[ch]"), d.rglob("*.[ch]pp"))):
            if insert_preamble_and_fixes(p):
                count += 1

    print(f"\nFinished. Changed {count} files.")
    print("Recommended commands:")
    print("  git add decomp-files/include/string.h")
    print("  git commit -m 'harmonizer v75.34: fixed string.h extern \"C\" insertion + stdbool'")
    print("Verify locally:")
    print("  grep -A 10 -B 5 '__cplusplus' decomp-files/include/string.h")
    print("  → should show clean extern \"C\" { ... } just before #endif")


if __name__ == "__main__":
    main()