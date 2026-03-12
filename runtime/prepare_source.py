#!/usr/bin/env python3
"""
SourceHarmonizer v75.66
BK AArch64 Android port — IDO/N64 decomp source → Clang/NDK compatibility

Resolving 'cannot combine with previous int' by virtualizing bool.h
and standardizing boolean logic across the codebase.
"""

import re
from pathlib import Path

# --- GLOBAL CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-v75.66-DSI */"
PREAMBLE = """\
{marker}
#ifndef _SH_TYPES_GUARD_
#define _SH_TYPES_GUARD_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// Direct N64/IDO Type Mapping
typedef uint8_t   u8;
typedef int8_t    s8;
typedef uint16_t  u16;
typedef int16_t   s16;
typedef uint32_t  u32;
typedef int32_t   s32;
typedef uint64_t  u64;
typedef int64_t   s64;
typedef float     f32;
typedef double    f64;

#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

// Block legacy bool redefinitions
#define _BOOL_H_
#define __bool_true_false_are_defined 1
#endif
""".format(marker=PREAMBLE_MARKER)

# ─────────────────────────────────────────────────────────────────────────────
# CORE REPAIR LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def _neutralize_bool_h(decomp_root: Path):
    """H11: Wipes the content of bool.h to prevent typedef int bool conflicts."""
    bool_h = decomp_root / "include" / "bool.h"
    if bool_h.exists():
        # Replace content with a simple guard to satisfy includes without errors
        content = "/* SH-v75.66: Virtualized to prevent Clang conflicts */\n#include <stdbool.h>\n"
        bool_h.write_text(content, encoding='utf-8')
        print("  [FIXED] bool.h neutralized")

def _reset_headers(decomp_root: Path):
    """H12: Standard SDK header cleanup."""
    pr_dir = decomp_root / "include" / "2.0L" / "PR"
    if not pr_dir.exists(): return

    for path in pr_dir.glob("*.h"):
        content = path.read_text(encoding='utf-8', errors='ignore')
        if any(v in content for v in ["SH-v75.64", "SH-v75.65"]):
            content = re.sub(r'/\* SH-v75\..*? \*/', '', content)
            path.write_text(content, encoding='utf-8')

# ─────────────────────────────────────────────────────────────────────────────
# SOURCE PROCESSING
# ─────────────────────────────────────────────────────────────────────────────

def process_c_file(path: Path):
    original = path.read_text(encoding='utf-8', errors='ignore')
    content = original
    
    # Remove all previous DSI markers
    content = re.sub(r'/\* SH-v75\.\d+-.*? \*/.*?(?=#ifndef _SH_TYPES_GUARD_|\n)', '', content, flags=re.DOTALL)
    # Ensure old guards are removed to apply new stdbool logic
    content = re.sub(r'#ifndef _SH_TYPES_GUARD_.*?#endif\n', '', content, flags=re.DOTALL)
    
    # Inject v75.66 DSI
    if PREAMBLE_MARKER not in content:
        content = PREAMBLE + content
    
    # Standard 64-bit pointer cast fix
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    
    if content != original:
        path.write_text(content, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path(__file__).resolve().parent.parent
    decomp_root = repo_root / "decomp-files"
    src_dir = decomp_root / "src"

    print(f"[>] SourceHarmonizer v75.66: Boolean Normalization Mode")
    
    _reset_headers(decomp_root)
    _neutralize_bool_h(decomp_root)
    
    modified_count = 0
    if src_dir.exists():
        for path in sorted(src_dir.rglob("*.c")):
            if process_c_file(path):
                modified_count += 1
                
    print(f"[+] Done. Processed {modified_count} source files.")

if __name__ == "__main__":
    main()
