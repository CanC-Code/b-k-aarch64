#!/usr/bin/env python3
import re
from pathlib import Path

"""
SourceHarmonizer v75.25 — Force preamble + diagnostics
Goal: make 100% sure BOOL is defined before any code is parsed
"""

PREAMBLE = """\
/* ──────────────────────────────────────────────── */
/* SourceHarmonizer v75.25 — FORCED Android compat   */
/* This block should appear near top of EVERY .c file */
/* ──────────────────────────────────────────────── */

#pragma message "SourceHarmonizer v75.25 preamble is ACTIVE in this file"

#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

#include <stddef.h>

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
/* End forced compat block v75.25                   */
/* ──────────────────────────────────────────────── */

"""

def insert_preamble(file_path: Path):
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Cannot read {file_path}: {e}")
        return False

    # If already has our pragma → assume it's done
    if "#pragma message \"SourceHarmonizer v75.25 preamble is ACTIVE" in content:
        print(f"  [SKIP] {file_path.name} — already has v75.25 preamble")
        return False

    # Simple strategy: always insert at the very beginning
    # This is more aggressive but guarantees visibility
    new_content = PREAMBLE + content

    try:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"  [MOD] {file_path.name} — preamble inserted")
        return True
    except Exception as e:
        print(f"Cannot write {file_path.name}: {e}")
        return False


def main():
    target_dir = Path("decomp-files/src")
    if not target_dir.is_dir():
        print(f"Error: {target_dir} not found")
        return

    print("SourceHarmonizer v75.25 — forcing preamble insertion")
    modified_count = 0

    for path in target_dir.rglob("*.c"):
        if insert_preamble(path):
            modified_count += 1

    print(f"\nDone. Modified {modified_count} files.")
    print("Next step: commit, push, retrigger CI")
    print("Look in build log for lines containing:")
    print("  'SourceHarmonizer v75.25 preamble is ACTIVE'")
    print("  'BOOL macro defined by SourceHarmonizer'")


if __name__ == "__main__":
    main()