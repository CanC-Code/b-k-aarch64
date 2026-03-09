#!/usr/bin/env python3
import re
from pathlib import Path
from itertools import chain

"""
SourceHarmonizer v75.38 — implicit bool decl fix + robust bool.h guard

Changelog v75.38:
- Added fix_implicit_bool_decls: injects forward declaration for audioManager_handleFrameMsg
  in code_1D00.c to resolve conflicting types (bool vs implicit int)
- Kept robust line-based bool.h guard logic from v75.37
- Bumped version and messages for clarity
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.38 — Android/NDK compat    */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.38 preamble is ACTIVE"

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
/* End compat block v75.38                          */
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
/* SourceHarmonizer v75.38 – C++ / NDK compatibility  */
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
    """Robust line-based guard insertion for bool.h"""
    if '__bool_true_false_are_defined' in content:
        print(f"  [BOOL_H SKIP] Already guarded → {file_path.name}")
        return content, False

    if 'typedef int bool' not in content:
        print(f"  [BOOL_H NO MATCH] No 'typedef int bool' found → {file_path.name}")
        return content, False

    lines = content.splitlines(keepends=True)
    new_lines = []
    guard_inserted = False
    guard_end_inserted = False

    for line in lines:
        stripped = line.strip()

        # Insert guard start right before typedef
        if 'typedef int bool' in stripped and not guard_inserted:
            new_lines.append('#ifndef __bool_true_false_are_defined\n')
            new_lines.append('#define false 0\n')
            new_lines.append('#define true  1\n')
            guard_inserted = True

        new_lines.append(line)

        # Insert guard end just before the file's closing #endif
        if stripped == '#endif' and guard_inserted and not guard_end_inserted:
            new_lines.insert(-1, '#endif /* __bool_true_false_are_defined */\n')
            guard_end_inserted = True

    if guard_inserted:
        new_content = ''.join(new_lines)
        print(f"  [BOOL_H FIXED] Inserted compatibility guard around typedef → {file_path.name}")
        return new_content, True

    print(f"  [BOOL_H NO INSERT] Guard not inserted → {file_path.name}")
    return content, False


def fix_implicit_bool_decls(file_path: Path, content: str) -> tuple[str, bool]:
    """
    Inject forward declarations for functions that return bool but are used before defined.
    Currently fixes audioManager_handleFrameMsg in code_1D00.c
    """
    if file_path.name != "code_1D00.c":
        return content, False

    if "audioManager_handleFrameMsg" not in content:
        return content, False

    # Avoid duplicate insertion
    if "bool audioManager_handleFrameMsg(AudioInfo *info, AudioInfo *prev_info);" in content:
        print(f"  [IMPLICIT_DECL SKIP] Forward decl already present → {file_path.name}")
        return content, False

    # Insert near top — after includes, before any code
    # Find position after last #include
    match = list(re.finditer(r'(?m)^#include.*?$', content))
    if match:
        last_include_end = match[-1].end()
        insert_pos = content.find('\n', last_include_end) + 1
        if insert_pos == 0:
            insert_pos = last_include_end + 1
    else:
        insert_pos = 0

    decl = """\
/* SourceHarmonizer v75.38: forward decl to fix implicit int vs bool conflict */
bool audioManager_handleFrameMsg(AudioInfo *info, AudioInfo *prev_info);

"""

    new_content = content[:insert_pos] + decl + content[insert_pos:]

    print(f"  [IMPLICIT_DECL FIXED] Added forward decl for audioManager_handleFrameMsg → {file_path.name}")
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

    # 1. Preamble for .c files
    if is_c:
        marker = "SourceHarmonizer v75.38 preamble is ACTIVE"
        if marker not in content:
            content = PREAMBLE + "\n" + content
            print(f"  [PREAMBLE+STDBOOL] Inserted in {file_path.name}")
            modified = True

    # 2. Guard custom bool.h
    if is_header and "bool.h" in fname_lower:
        new_content, changed = guard_custom_bool_h(file_path, content)
        if changed:
            content = new_content
            modified = True

    # 3. Fix implicit bool function declarations
    if is_c:
        new_content, changed = fix_implicit_bool_decls(file_path, content)
        if changed:
            content = new_content
            modified = True

    # 4. string.h fix
    if is_header and "string.h" in fname_lower:
        new_content, changed = harmonize_string_h(file_path, content)
        if changed:
            content = new_content
            modified = True

    # 5. C++ safety net
    if is_cpp:
        content = re.sub(
            r'^\s*#include\s*["<]string\.h[">].*$',
            r'// SourceHarmonizer v75.38: disabled conflicting decomp string.h',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )

        inject = '\n// SourceHarmonizer v75.38: force standard headers\n#include <cstddef>\n#include <cstring>\n#include <stdbool.h>\n\n'
        if "SourceHarmonizer v75.38 preamble" in content:
            content = re.sub(
                r'(/\* End compat block v75\.38.*?\*/\s*)',
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

    print("SourceHarmonizer v75.38 running – implicit bool decl fix + bool.h guard")

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
    print("  git add decomp-files/src/core1/code_1D00.c decomp-files/include/bool.h")
    print("  git commit -m 'harmonizer v75.38: fix implicit bool decl in code_1D00.c'")
    print("Verify locally:")
    print("  grep -A 5 'audioManager_handleFrameMsg' decomp-files/src/core1/code_1D00.c")
    print("  → should show the forward declaration near top")


if __name__ == "__main__":
    main()