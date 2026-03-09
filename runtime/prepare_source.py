#!/usr/bin/env python3
import re
from pathlib import Path
from itertools import chain

"""
SourceHarmonizer v75.35 — bool.h conflict fix + continued string.h safety

Changelog v75.35:
- Automatically guards custom bool.h typedef with #ifndef __bool_true_false_are_defined
  → prevents conflict with NDK <stdbool.h>
- Keeps forcing #include <stdbool.h> in .c files (native _Bool is better)
- No more typedef int bool; redefinition errors
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.35 — Android/NDK compat    */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.35 preamble is ACTIVE"

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
/* End compat block v75.35                          */
/* ──────────────────────────────────────────────── */
"""

def count_ifdef_endif(content: str) -> tuple[int, int, bool]:
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
        print(f"  [STRING_H WARN] Unbalanced guard ({if_count}/{endif_count}) → attempting repair")

    last_endif_matches = list(re.finditer(r'(?m)^#endif\b.*?$', content))
    if not last_endif_matches:
        print(f"  [STRING_H WARN] No #endif found → appending block")
        insert_pos = len(content)
    else:
        insert_pos = last_endif_matches[-1].start()

    insert_text = """
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.35 – C++ / NDK compatibility  */
/* ──────────────────────────────────────────────── */

#ifdef __cplusplus
extern "C" {
#endif

"""

    new_content = content[:insert_pos] + insert_text + content[insert_pos:]

    new_content = re.sub(
        r'(#endif\s*(?:/\*.*?\*/)?\s*$)',
        r'#ifdef __cplusplus\n}\n#endif\n\1',
        new_content,
        flags=re.DOTALL | re.MULTILINE,
        count=1
    )

    print(f"  [STRING_H FIXED] Inserted extern \"C\" guard → {file_path.name}")
    return new_content, True


def guard_custom_bool_h(file_path: Path, content: str) -> tuple[str, bool]:
    """Wrap custom typedef int bool; with compatibility guard"""
    if not re.search(r'typedef\s+int\s+bool\s*;', content):
        return content, False

    # Pattern to find the typedef + optional defines
    pat = re.compile(
        r'(\s*typedef\s+int\s+bool\s*;\s*)'
        r'(?:\s*#define\s+(?:false|FALSE)\s+\d\s*)*'
        r'(?:\s*#define\s+(?:true|TRUE)\s+\d\s*)*',
        re.DOTALL | re.IGNORECASE
    )

    def repl(m):
        return f"""\
#ifndef __bool_true_false_are_defined
{m.group(0).strip()}
#endif
"""

    new_content = pat.sub(repl, content)

    if new_content != content:
        print(f"  [BOOL_H GUARD] Wrapped custom typedef int bool; → {file_path.name}")
        return new_content, True
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

    # 1. Preamble for .c files
    if is_c:
        marker = "SourceHarmonizer v75.35 preamble is ACTIVE"
        if marker not in content:
            content = PREAMBLE + "\n" + content
            print(f"  [PREAMBLE+STDBOOL] Inserted in {file_path.name}")
            modified = True

    # 2. Guard custom bool.h if this is the file
    if is_header and "bool.h" in fname_lower:
        new_content, changed = guard_custom_bool_h(file_path, content)
        if changed:
            content = new_content
            modified = True

    # 3. string.h fix
    if is_header and "string.h" in fname_lower:
        new_content, changed = harmonize_string_h(file_path, content)
        if changed:
            content = new_content
            modified = True

    # 4. C++ safety net (disable decomp string.h + force standards)
    if is_cpp:
        content = re.sub(
            r'^\s*#include\s*["<]string\.h[">].*$',
            r'// SourceHarmonizer v75.35: disabled conflicting decomp string.h',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )

        inject = '\n// SourceHarmonizer v75.35: force standard headers\n#include <cstddef>\n#include <cstring>\n#include <stdbool.h>\n\n'
        if "SourceHarmonizer v75.35 preamble" in content:
            content = re.sub(
                r'(/\* End compat block v75\.35.*?\*/\s*)',
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

    print("SourceHarmonizer v75.35 running – bool.h guarded + string.h safety")

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
    print("  git add decomp-files/include/bool.h")
    print("  git commit -m 'harmonizer v75.35: guard custom bool.h against NDK stdbool.h'")
    print("Verify locally:")
    print("  grep -A 5 '__bool_true_false_are_defined' decomp-files/include/bool.h")
    print("  → should show the guard around typedef int bool;")


if __name__ == "__main__":
    main()