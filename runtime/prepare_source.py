#!/usr/bin/env python3
"""
SourceHarmonizer v75.62
BK AArch64 Android port — IDO/N64 decomp source → Clang/NDK compatibility

This script patches the decomp-files/src and decomp-files/include directories 
to resolve type conflicts, 64-bit pointer alignment issues, and recursive 
header inclusions that crash the NDK/Ninja build process.
"""

import re
from pathlib import Path

# --- GLOBAL CONFIGURATION & KEYWORDS ---
_C_KEYWORDS = {
    'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do',
    'break', 'continue', 'case', 'default', 'goto', 'struct', 'union',
    'enum', 'static', 'extern', 'const', 'volatile', 'inline', 'typedef',
    'register', 'auto', 'void', 'int', 'char', 'short', 'long', 'float',
    'double', 'unsigned', 'signed', 'bool',
}
_STD_C = {
    'main', 'memcpy', 'memset', 'memmove', 'strlen', 'strcpy', 'strcmp', 
    'sprintf', 'printf', 'malloc', 'free', 'sin', 'cos', 'sqrt', 'abs',
}
_SDK_PREFIXES = ('os', 'gu', 'al', 'gS', 'gD', 'gd', '__os', 'sp', 'dp', 'rmon')
_STORAGE_QUALS = {'static', 'extern', 'inline', 'const', 'volatile', '__attribute__'}

# --- PREAMBLE FOR .C FILES ---
PREAMBLE_MARKER = "/* SH-v75.62-preamble */"
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
# NEW HEADER PASSES (H6, H7, H8) - THE FIX FOR "GFX" & "REDEFINITION"
# ─────────────────────────────────────────────────────────────────────────────

def _fix_ultratypes_standardization(decomp_root: Path):
    """H6: Forces N64 types to map to C99 stdint types to prevent NDK conflicts."""
    path = decomp_root / "include" / "2.0L" / "PR" / "ultratypes.h"
    if not path.exists(): return
    content = path.read_text(encoding='utf-8', errors='ignore')
    if "v75.62 Standard Type Mapping" in content: return

    mapping = {
        r'typedef\s+unsigned\s+char\s+u8;':  'typedef uint8_t u8;',
        r'typedef\s+signed\s+char\s+s8;':    'typedef int8_t s8;',
        r'typedef\s+unsigned\s+short\s+u16;': 'typedef uint16_t u16;',
        r'typedef\s+short\s+s16;':           'typedef int16_t s16;',
        r'typedef\s+unsigned\s+int\s+u32;':   'typedef uint32_t u32;',
        r'typedef\s+int\s+s32;':            'typedef int32_t s32;',
        r'typedef\s+unsigned\s+long\s+long\s+u64;': 'typedef uint64_t u64;',
        r'typedef\s+long\s+long\s+s64;':     'typedef int64_t s64;',
    }
    
    new_content = "/* SH: v75.62 Standard Type Mapping */\n#include <stdint.h>\n"
    temp_content = content
    for old, new in mapping.items():
        temp_content = re.sub(old, new, temp_content)
    
    path.write_text(new_content + temp_content, encoding='utf-8')
    print(f"  [PATCHED] ultratypes.h standardized")

def _fix_gbi_abi_visibility(decomp_root: Path):
    """H7: Forward declares Acmd in GBI to stop circular include dependency."""
    gbi_path = decomp_root / "include" / "2.0L" / "PR" / "gbi.h"
    if not gbi_path.exists(): return
    content = gbi_path.read_text(encoding='utf-8')
    if "struct Acmd;" not in content:
        content = content.replace("#define _GBI_H_", "#define _GBI_H_\nstruct Acmd;")
        gbi_path.write_text(content)
        print("  [PATCHED] gbi.h visibility fixed")

def _sanitize_audio_headers(decomp_root: Path):
    """H8: Guards AudioInfo to prevent multiple redefinition errors."""
    audio_h = decomp_root / "include" / "audio.h"
    if not audio_h.exists(): return
    content = audio_h.read_text(encoding='utf-8')
    if "_AUDIO_INFO_GUARD" not in content:
        content = re.sub(r'(typedef\s+struct\s+AudioInfo_s\s+\{)', 
                         r'#ifndef _AUDIO_INFO_GUARD\n#define _AUDIO_INFO_GUARD\n\1', content)
        content = re.sub(r'(\}\s*AudioInfo;)', r'\1\n#endif', content)
        audio_h.write_text(content)
        print("  [PATCHED] audio.h guarded")

# ─────────────────────────────────────────────────────────────────────────────
# CORE LOGIC FOR .C FILES
# ─────────────────────────────────────────────────────────────────────────────

def _fix_pointer_to_int_casts(content: str) -> str:
    """Fixes 64-bit pointer truncation errors (e.g., casting ptr to u32)."""
    return re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)

def process_c_file(path: Path):
    original = path.read_text(encoding='utf-8', errors='ignore')
    content = original
    
    if PREAMBLE_MARKER not in content:
        content = PREAMBLE + content
    
    # Standard Harmonizer Logic
    content = _fix_pointer_to_int_casts(content)
    # Add your existing regex passes (array_inits, static_conflicts, etc) here
    
    if content != original:
        path.write_text(content, encoding='utf-8')
        return True
    return False

# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────

def main():
    repo_root = Path(__file__).resolve().parent.parent
    decomp_root = repo_root / "decomp-files"
    src_dir = decomp_root / "src"

    print(f"[>] SourceHarmonizer v75.62 Starting...")
    
    # 1. Fix Headers first
    _fix_ultratypes_standardization(decomp_root)
    _fix_gbi_abi_visibility(decomp_root)
    _sanitize_audio_headers(decomp_root)
    
    # 2. Process all C files
    modified_count = 0
    for path in sorted(src_dir.rglob("*.c")):
        if process_c_file(path):
            modified_count += 1
            print(f"  [MOD] {path.name}")
            
    print(f"[+] Done. Modified {modified_count} files.")

if __name__ == "__main__":
    main()
