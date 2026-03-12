#!/usr/bin/env python3
"""
SourceHarmonizer v75.65
BK AArch64 Android port — IDO/N64 decomp source → Clang/NDK compatibility

Direct Source Injection (DSI) to resolve persistent 'unknown type name' 
errors in nested SDK headers.
"""

import re
from pathlib import Path

# --- GLOBAL CONFIGURATION ---
# v75.65 uses a "Bulletproof" type block injected directly into source files
PREAMBLE_MARKER = "/* SH-v75.65-DSI */"
PREAMBLE = """\
{marker}
#ifndef _SH_TYPES_GUARD_
#define _SH_TYPES_GUARD_
#include <stdint.h>
#include <stddef.h>

// Direct N64/IDO Type Mapping for Clang
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

#ifndef __bool_true_false_are_defined
#  define __bool_true_false_are_defined 1
#  ifndef bool
#    define bool _Bool
#  endif
#endif
#endif
""".format(marker=PREAMBLE_MARKER)

# ─────────────────────────────────────────────────────────────────────────────
# SDK HEADER CLEANUP
# ─────────────────────────────────────────────────────────────────────────────

def _reset_and_guard_headers(decomp_root: Path):
    """H10: Cleans up previous injection attempts in headers to prevent 'redefinition' errors."""
    pr_dir = decomp_root / "include" / "2.0L" / "PR"
    if not pr_dir.exists(): return

    for path in pr_dir.glob("*.h"):
        content = path.read_text(encoding='utf-8', errors='ignore')
        # Remove previous versions' brute-force includes to avoid loops
        if "SH-v75.64" in content or "#include <PR/ultratypes.h>" in content[:50]:
            content = re.sub(r'#include <PR/ultratypes\.h>\s*', '', content)
            path.write_text(content, encoding='utf-8')

def _fix_ultratypes_final(decomp_root: Path):
    """H6: Ensures ultratypes.h itself doesn't conflict with our DSI."""
    path = decomp_root / "include" / "2.0L" / "PR" / "ultratypes.h"
    if not path.exists(): return
    
    # We wrap the entire file in a guard that respects our DSI
    content = """\
#ifndef _SH_TYPES_GUARD_
/* Standard ultratypes fallback */
#ifndef _ULTRATYPES_H_
#define _ULTRATYPES_H_
typedef unsigned char      u8;
typedef signed char        s8;
typedef unsigned short     u16;
typedef short              s16;
typedef unsigned int       u32;
typedef int                s32;
typedef unsigned long long u64;
typedef long long          s64;
typedef float              f32;
typedef double             f64;
#endif
#endif
"""
    path.write_text(content, encoding='utf-8')
    print("  [FIXED] ultratypes.h virtualized")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────

def process_c_file(path: Path):
    original = path.read_text(encoding='utf-8', errors='ignore')
    content = original
    
    # Remove old preambles
    content = re.sub(r'/\* SH-v75\.\d+-.*? \*/.*?(?=\n)', '', content, flags=re.DOTALL)
    
    # Inject v75.65 DSI at the very top
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

    print(f"[>] SourceHarmonizer v75.65: Direct Source Injection Mode")
    
    # 1. Clean and Prepare SDK
    _reset_and_guard_headers(decomp_root)
    _fix_ultratypes_final(decomp_root)
    
    # 2. Source Code Pass
    modified_count = 0
    if src_dir.exists():
        for path in sorted(src_dir.rglob("*.c")):
            if process_c_file(path):
                modified_count += 1
                
    print(f"[+] Done. Injected DSI into {modified_count} files.")

if __name__ == "__main__":
    main()
