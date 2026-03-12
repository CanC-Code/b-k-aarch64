#!/usr/bin/env python3
"""
SourceHarmonizer v75.63
BK AArch64 Android port — IDO/N64 decomp source → Clang/NDK compatibility

This script resolves "unknown type name" errors by standardizing ultratypes.h
and forcing its inclusion across the PR header stack.
"""

import re
from pathlib import Path

# --- GLOBAL CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-v75.63-preamble */"
PREAMBLE = """\
{marker}
#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif
#include <stddef.h>
#include <string.h>
#include <stdint.h>

#ifndef __bool_true_false_are_defined
#  define __bool_true_false_are_defined 1
#  ifndef bool
#    define bool _Bool
#  endif
#endif

#ifndef BOOL
#  define BOOL(x) (!!(x))
#endif
""".format(marker=PREAMBLE_MARKER)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER REPAIR LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def _fix_ultratypes_standardization(decomp_root: Path):
    """H6: Maps N64 types to C99 stdint types to prevent NDK/64-bit conflicts."""
    path = decomp_root / "include" / "2.0L" / "PR" / "ultratypes.h"
    if not path.exists(): return
    content = path.read_text(encoding='utf-8', errors='ignore')
    if "v75.63 Standard Type Mapping" in content: return

    mapping = {
        r'typedef\s+unsigned\s+char\s+u8;':  'typedef uint8_t u8;',
        r'typedef\s+signed\s+char\s+s8;':    'typedef int8_t s8;',
        r'typedef\s+unsigned\s+short\s+u16;': 'typedef uint16_t u16;',
        r'typedef\s+short\s+s16;':           'typedef int16_t s16;',
        r'typedef\s+unsigned\s+int\s+u32;':   'typedef uint32_t u32;',
        r'typedef\s+int\s+s32;':            'typedef int32_t s32;',
        r'typedef\s+unsigned\s+long\s+long\s+u64;': 'typedef uint64_t u64;',
        r'typedef\s+long\s+long\s+s64;':     'typedef int64_t s64;',
        r'typedef\s+float\s+f32;':           'typedef float f32;',
        r'typedef\s+double\s+f64;':          'typedef double f64;',
    }
    
    header = "/* SH: v75.63 Standard Type Mapping */\n#include <stdint.h>\n"
    for old, new in mapping.items():
        content = re.sub(old, new, content)
    
    path.write_text(header + content, encoding='utf-8')
    print(f"  [PATCHED] ultratypes.h standardized")

def _force_ultratypes_inclusion(decomp_root: Path):
    """H9: Ensures os_thread.h and others have types by forcing ultratypes.h inclusion."""
    pr_include_dir = decomp_root / "include" / "2.0L" / "PR"
    target_headers = ["os_thread.h", "os_message.h", "os_pi.h", "os_vi.h"]
    
    for header_name in target_headers:
        path = pr_include_dir / header_name
        if not path.exists(): continue
        
        content = path.read_text(encoding='utf-8', errors='ignore')
        if "ultratypes.h" not in content:
            # Insert after the header guard if it exists, otherwise at the top
            guard_match = re.search(r'#define\s+_\w+_H_', content)
            if guard_match:
                insertion_point = guard_match.end()
                content = content[:insertion_point] + "\n#include <PR/ultratypes.h>" + content[insertion_point:]
            else:
                content = "#include <PR/ultratypes.h>\n" + content
            
            path.write_text(content, encoding='utf-8')
            print(f"  [FIXED] Forced ultratypes.h into {header_name}")

def _fix_gbi_abi_visibility(decomp_root: Path):
    """H7: Forward declares Acmd in GBI to stop circular include dependency."""
    gbi_path = decomp_root / "include" / "2.0L" / "PR" / "gbi.h"
    if not gbi_path.exists(): return
    content = gbi_path.read_text(encoding='utf-8')
    if "struct Acmd;" not in content:
        content = content.replace("#define _GBI_H_", "#define _GBI_H_\nstruct Acmd;")
        gbi_path.write_text(content)
        print("  [PATCHED] gbi.h visibility fixed")

# ─────────────────────────────────────────────────────────────────────────────
# FILE PROCESSING LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def _fix_pointer_to_int_casts(content: str) -> str:
    """Fixes 64-bit pointer truncation errors (e.g., casting ptr to u32)."""
    return re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)

def process_c_file(path: Path):
    original = path.read_text(encoding='utf-8', errors='ignore')
    content = original
    
    if PREAMBLE_MARKER not in content:
        content = PREAMBLE + content
    
    content = _fix_pointer_to_int_casts(content)
    
    if content != original:
        path.write_text(content, encoding='utf-8')
        return True
    return False

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Adjusting path to find decomp-files relative to the script location
    repo_root = Path(__file__).resolve().parent.parent
    decomp_root = repo_root / "decomp-files"
    src_dir = decomp_root / "src"

    print(f"[>] SourceHarmonizer v75.63 Starting...")
    
    # 1. Critical Header Fixes
    _fix_ultratypes_standardization(decomp_root)
    _force_ultratypes_inclusion(decomp_root)
    _fix_gbi_abi_visibility(decomp_root)
    
    # 2. Source Code Fixes
    modified_count = 0
    if src_dir.exists():
        for path in sorted(src_dir.rglob("*.c")):
            if process_c_file(path):
                modified_count += 1
                print(f"  [MOD] {path.name}")
            
    print(f"[+] Done. Modified {modified_count} source files.")

if __name__ == "__main__":
    main()
