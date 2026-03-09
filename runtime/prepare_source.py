#!/usr/bin/env python3
import re
from pathlib import Path
from itertools import chain

"""
SourceHarmonizer v75.39 — late forward decl + robust bool.h guard

Changelog v75.39:
- Moved forward decl insertion to AFTER last #include in code_1D00.c
  → ensures AudioInfo is known before declaring audioManager_handleFrameMsg
- Prevents "unknown type name 'AudioInfo'" error
- Improved duplicate check
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.39 — Android/NDK compat    */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.39 preamble is ACTIVE"

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
/* End compat block v75.39                          */
/* ──────────────────────────────────────────────── */
"""

# ... (keep count_ifdef_endif, harmonize_string_h, guard_custom_bool_h unchanged from your last version)

def fix_implicit_bool_decls(file_path: Path, content: str) -> tuple[str, bool]:
    """
    Inject forward declarations for functions that return bool but are used before defined.
    Places declaration AFTER last #include to ensure types like AudioInfo are visible.
    """
    if file_path.name != "code_1D00.c":
        return content, False

    if "audioManager_handleFrameMsg" not in content:
        return content, False

    # Avoid duplicate
    if "/* SourceHarmonizer: forward decl for audioManager_handleFrameMsg */" in content:
        print(f"  [IMPLICIT_DECL SKIP] Forward decl already present → {file_path.name}")
        return content, False

    # Find position AFTER the last #include
    matches = list(re.finditer(r'(?m)^#include\s+.*?$', content))
    if matches:
        insert_pos = matches[-1].end()
        # Move to the next line start
        next_line_start = content.find('\n', insert_pos)
        if next_line_start != -1:
            insert_pos = next_line_start + 1
        else:
            insert_pos += 1  # fallback
    else:
        insert_pos = 0  # very beginning if no includes

    decl = """\
/* SourceHarmonizer v75.39: forward decl to fix implicit int vs bool conflict */
bool audioManager_handleFrameMsg(AudioInfo *info, AudioInfo *prev_info);

"""

    new_content = content[:insert_pos] + decl + content[insert_pos:]

    print(f"  [IMPLICIT_DECL FIXED] Late forward decl inserted after last #include → {file_path.name}")
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
        marker = "SourceHarmonizer v75.39 preamble is ACTIVE"
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

    # 3. Fix implicit bool function declarations (NEW POSITION: after includes)
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
            r'// SourceHarmonizer v75.39: disabled conflicting decomp string.h',
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )

        inject = '\n// SourceHarmonizer v75.39: force standard headers\n#include <cstddef>\n#include <cstring>\n#include <stdbool.h>\n\n'
        if "SourceHarmonizer v75.39 preamble" in content:
            content = re.sub(
                r'(/\* End compat block v75\.39.*?\*/\s*)',
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

    print("SourceHarmonizer v75.39 running – late forward decl fix + bool.h guard")

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
    print("  git add decomp-files/src/core1/code_1D00.c")
    print("  git commit -m 'harmonizer v75.39: late forward decl for audioManager_handleFrameMsg'")
    print("Verify locally:")
    print("  grep -A 5 'audioManager_handleFrameMsg' decomp-files/src/core1/code_1D00.c")
    print("  → should show the forward decl after last #include")


if __name__ == "__main__":
    main()