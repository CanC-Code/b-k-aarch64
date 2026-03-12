#!/usr/bin/env python3
"""
SourceHarmonizer v75.64
BK AArch64 Android port — IDO/N64 decomp source → Clang/NDK compatibility

Aggressive fix for "unknown type name" in SDK headers by forcing early 
inclusion of standardized types and resolving float/double conflicts.
"""

import re
from pathlib import Path

# --- GLOBAL CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-v75.64-preamble */"
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
""".format(marker=PREAMBLE_MARKER)

# ─────────────────────────────────────────────────────────────────────────────
# SDK HEADER REPAIR (THE "NUCLEAR" OPTION)
# ─────────────────────────────────────────────────────────────────────────────

def _fix_ultratypes_standardization(decomp_root: Path):
    """H6: Maps N64 types to C99 stdint types. Updated for v75.64."""
    path = decomp_root / "include" / "2.0L" / "PR" / "ultratypes.h"
    if not path.exists(): return
    content = path.read_text(encoding='utf-8', errors='ignore')
    if "v75.64 Standard Type Mapping" in content: return

    # Ensure stdint is available
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
    
    for old, new in mapping.items():
        content = re.sub(old, new, content)
    
    # Add guard to prevent circular issues with the force-include pass
    header = "/* SH: v75.64 Standard Type Mapping */\n#ifndef _ULTRATYPES_H_SH_\n#define _ULTRATYPES_H_SH_\n#include <stdint.h>\n"
    footer = "\n#endif /* _ULTRATYPES_H_SH_ */"
    
    path.write_text(header + content + footer, encoding='utf-8')
    print(f"  [PATCHED] ultratypes.h standardized and guarded")

def _force_global_sdk_types(decomp_root: Path):
    """H9: Recursively forces every PR header to include ultratypes.h first."""
    pr_dir = decomp_root / "include" / "2.0L" / "PR"
    if not pr_dir.exists(): return

    for path in pr_dir.glob("*.h"):
        if path.name == "ultratypes.h": continue
        
        content = path.read_text(encoding='utf-8', errors='ignore')
        if "ultratypes.h" not in content:
            # We insert it at the absolute top of the file to beat the type usage
            new_content = "#include <PR/ultratypes.h>\n" + content
            path.write_text(new_content, encoding='utf-8')
            print(f"  [FIXED] Global Type Force: {path.name}")

def _fix_gbi_abi_visibility(decomp_root: Path):
    """H7: Forward declares Acmd to stop circular dependencies in graphics headers."""
    gbi_path = decomp_root / "include" / "2.0L" / "PR" / "gbi.h"
    if not gbi_path.exists(): return
    content = gbi_path.read_text(encoding='utf-8')
    if "struct Acmd;" not in content:
        content = content.replace("#define _GBI_H_", "#define _GBI_H_\nstruct Acmd;")
        gbi_path.write_text(content)
        print("  [PATCHED] gbi.h visibility fixed")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────

def process_c_file(path: Path):
    original = path.read_text(encoding='utf-8', errors='ignore')
    content = original
    
    if PREAMBLE_MARKER not in content:
        content = PREAMBLE + content
    
    # Fix pointer truncation for 64-bit Android
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    
    if content != original:
        path.write_text(content, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path(__file__).resolve().parent.parent
    decomp_root = repo_root / "decomp-files"
    src_dir = decomp_root / "src"

    print(f"[>] SourceHarmonizer v75.64 Starting...")
    
    # 1. SDK Infrastructure Repair
    _fix_ultratypes_standardization(decomp_root)
    _force_global_sdk_types(decomp_root)
    _fix_gbi_abi_visibility(decomp_root)
    
    # 2. Source Code Pass
    modified_count = 0
    if src_dir.exists():
        for path in sorted(src_dir.rglob("*.c")):
            if process_c_file(path):
                modified_count += 1
                print(f"  [MOD] {path.name}")
            
    print(f"[+] Done. Modified {modified_count} source files.")

if __name__ == "__main__":
    main()
