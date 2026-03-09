#!/usr/bin/env python3
import re
from pathlib import Path

"""
SourceHarmonizer v75.34 — Fix unterminated #ifndef + ensure bool is defined

Changelog v75.34:
- More defensive string.h rewriting: always add #endif if missing
- Add #include <stdbool.h> very early in string.h (guarded)
- If string.h already has extern "C", we skip re-wrapping but still force <stdbool.h>
- Clean up trailing garbage / mismatched guards
- Better fallback when no classic guard is found
- Force #include <stdbool.h> in .c files that include core1/ml.h or framebufferdraw.h
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.34 — Android NDK compat fix */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.34 is ACTIVE"

#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

#include <stddef.h>
#include <stdbool.h>   /* force bool type availability */

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

def harmonize_file(file_path: Path) -> bool:
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Cannot read {file_path}: {e}")
        return False

    original = text
    changed = False

    fname_lower = file_path.name.lower()
    is_c = file_path.suffix == ".c"
    is_h = file_path.suffix == ".h"
    is_cpp = file_path.suffix in {".cpp", ".hpp", ".cc", ".cxx", ".c++"}

    # ────────────────────────────────────────────────
    # 1. Preamble for .c files
    # ────────────────────────────────────────────────
    if is_c:
        if "SourceHarmonizer v75.34 is ACTIVE" not in text:
            text = PREAMBLE.rstrip() + "\n\n" + text.lstrip()
            changed = True
            print(f"  [PREAMBLE] added in {file_path.name}")

    # ────────────────────────────────────────────────
    # 2. Force <stdbool.h> in files that need bool but break early
    # ────────────────────────────────────────────────
    needs_bool = any(x in text for x in [
        "framebufferdraw.h", "ml.h", "bool alpha_enabled", "bool dim",
        "bool ml_timer_update", "bool ml_isZero_vec3f"
    ])

    if (is_c or is_h) and needs_bool:
        # Insert right after any existing #includes or at top
        bool_include = '#include <stdbool.h>   /* forced by harmonizer */\n'
        if bool_include not in text:
            # Try after first #include block
            match = re.search(r'((?:^\s*#include\s+.*?\n)+)', text, re.MULTILINE)
            if match:
                pos = match.end()
                text = text[:pos] + bool_include + text[pos:]
            else:
                text = bool_include + text
            changed = True
            print(f"  [BOOL] forced <stdbool.h> in {file_path.name}")

    # ────────────────────────────────────────────────
    # 3. Robust rewrite of string.h
    # ────────────────────────────────────────────────
    if is_h and "string.h" in fname_lower:
        # Check if already has extern "C" block
        has_extern_c = re.search(r'extern\s*"C"\s*{', text, re.IGNORECASE)

        # Remove previous broken wrapping attempts (common failure patterns)
        text = re.sub(
            r'(/\*\s*SourceHarmonizer.*?extern "C".*?\*/\s*){2,}',
            r'/* Cleaned duplicate harmonizer wrap */\n',
            text, flags=re.DOTALL | re.IGNORECASE
        )

        # Try to fix incomplete #endif
        if text.count('#ifndef') > text.count('#endif'):
            text += "\n#endif  /* forced closing by harmonizer */\n"

        # Force <stdbool.h> near top of string.h
        if '#include <stdbool.h>' not in text:
            text = '#include <stdbool.h>   /* harmonizer fix */\n' + text

        if not has_extern_c:
            # Common guard patterns
            guard_re = re.compile(
                r'((?:#ifndef\s+\w+\s+#define\s+\w+\s*|#pragma\s+once\s*))(.*?)(#endif\s*(?:/\*.*?\*/)?\s*$)',
                re.DOTALL | re.IGNORECASE | re.MULTILINE
            )

            m = guard_re.search(text)
            if m:
                before = m.group(1)
                body = m.group(2).strip()
                after = text[m.end():].strip()

                wrapped = f"""{before}
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.34 — C++/NDK compatibility  */
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
                text = wrapped
                changed = True
                print(f"  [STRING_H] wrapped with extern \"C\" in {file_path.name}")
            else:
                # Fallback: wrap almost everything after first line
                lines = text.splitlines(True)
                if len(lines) > 3:
                    header = "".join(lines[:3])
                    body = "".join(lines[3:])
                    text = f"""{header}
/* SourceHarmonizer fallback wrap v75.34 */
#ifdef __cplusplus
extern "C" {{
#endif

{body}
#ifdef __cplusplus
}}
#endif
"""
                    changed = True
                    print(f"  [STRING_H] fallback extern \"C\" wrap in {file_path.name}")

    # ────────────────────────────────────────────────
    # 4. C++ files safety net (same as before)
    # ────────────────────────────────────────────────
    if is_cpp:
        # Disable conflicting #include <string.h>
        text = re.sub(
            r'^\s*#include\s*["<]string\.h[">].*$',
            r'// harmonizer v75.34: disabled conflicting decomp string.h',
            text,
            flags=re.MULTILINE | re.IGNORECASE
        )

        # Force standard headers early
        inject = """// harmonizer v75.34: force standard headers
#include <cstddef>
#include <cstring>
#include <stdbool.h>

"""
        if "SourceHarmonizer v75.34 is ACTIVE" in text:
            text = re.sub(
                r'(/\* End compat block v75\.34.*?\*/\s*)',
                rf'\1{inject}',
                text,
                flags=re.DOTALL | re.IGNORECASE
            )
        else:
            text = inject + text

        changed = True
        print(f"  [C++] forced std headers in {file_path.name}")

    # ────────────────────────────────────────────────
    # Save if changed
    # ────────────────────────────────────────────────
    if changed:
        try:
            file_path.write_text(text, encoding="utf-8")
            print(f"  → Modified: {file_path.name}")
            return True
        except Exception as e:
            print(f"Cannot write {file_path}: {e}")
            return False
    else:
        print(f"  → No change: {file_path.name}")
        return False


def main():
    roots = [
        Path("decomp-files/src"),
        Path("decomp-files/include"),
        Path("Android/app/src/main/cpp"),
    ]

    print("SourceHarmonizer v75.34 — fixing string.h guard + bool type")

    modified = 0

    for root in roots:
        if not root.is_dir():
            print(f"  Dir missing: {root}")
            continue
        for p in sorted(root.rglob("*.[ch]") + root.rglob("*.[ch]pp")):
            if harmonize_file(p):
                modified += 1

    print(f"\nFinished. Modified {modified} files.")
    print("Next steps:")
    print("  git add decomp-files/include/string.h")
    print("  git commit -m 'harmonizer v75.34: fix unterminated #ifndef + force bool'")
    print("  git push && re-run CI")
    print("")
    print("Quick check:")
    print("  grep -A 15 STRING_H decomp-files/include/string.h")
    print("  → should have proper #endif and extern \"C\" block")


if __name__ == "__main__":
    main()