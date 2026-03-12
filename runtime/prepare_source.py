#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-v79.0-AUTOMORPH */"

def neutralize_bool_header(decomp_root: Path):
    """
    Physically overwrites the project's bool.h to prevent the 'int' typedef 
    conflict with Clang's stdbool.h.
    """
    bool_h = decomp_root / "include" / "bool.h"
    if bool_h.exists():
        content = bool_h.read_text(encoding='utf-8')
        if "typedef int bool;" in content:
            # We comment out the legacy typedef and inject stdbool.h
            content = content.replace("typedef int bool;", "/* typedef int bool; replaced for Android */\n#include <stdbool.h>")
            bool_h.write_text(content, encoding='utf-8')
            print("  [PATCHED] include/bool.h neutralized.")

def fix_audio_struct_redefinitions(decomp_root: Path):
    """
    Fixes the 'typedef redefinition with different types' error in synthInternals.h
    by ensuring the struct tag matches the typedef name exactly, neutralizing the '_s' suffix pattern.
    """
    synth_h = decomp_root / "include" / "synthInternals.h"
    if synth_h.exists():
        content = synth_h.read_text(encoding='utf-8')
        
        # Replace 'typedef struct ALFilter_s {' with 'typedef struct ALFilter {'
        content = re.sub(r'typedef\s+struct\s+ALFilter_s\s*\{', 'typedef struct ALFilter {', content)
        # Replace 'typedef struct ALAuxBus_s {' with 'typedef struct ALAuxBus {'
        content = re.sub(r'typedef\s+struct\s+ALAuxBus_s\s*\{', 'typedef struct ALAuxBus {', content)
        
        synth_h.write_text(content, encoding='utf-8')
        print("  [PATCHED] include/synthInternals.h struct tags normalized.")

def synthesize_preamble():
    return f"""{PREAMBLE_MARKER}
#ifndef _SH_DYNAMIC_GUARD_
#define _SH_DYNAMIC_GUARD_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// Force-inject N64 Primitives FIRST
#ifndef _SH_PRIMITIVES_
#define _SH_PRIMITIVES_
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
#endif

#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

// Safe Forward Declarations for Audio Types (Normalized in v79.0)
struct ALFilter;
typedef struct ALFilter ALFilter;
struct ALAuxBus;
typedef struct ALAuxBus ALAuxBus;
struct ALCSPlayer;
typedef struct ALCSPlayer ALCSPlayer;
struct N_ALCSPlayer;
typedef struct N_ALCSPlayer N_ALCSPlayer;
struct ALSeqFile;
typedef struct ALSeqFile ALSeqFile;
struct ALBankFile;
typedef struct ALBankFile ALBankFile;

#endif
"""

def apply_dynamic_fixes(content):
    # 64-bit Pointer Truncation Fixes
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    content = re.sub(r'\(u32\)\s*\((.*?)\)', r'(u32)(uintptr_t)(\1)', content)
    
    # Neutralize inline legacy bool typedefs inside .c files
    content = re.sub(r'^typedef\s+int\s+bool;', r'/* typedef int bool; */', content, flags=re.M)
    return content

def process_file(path):
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    
    # Clean old Harmonizer versions
    content = re.sub(r'/\* SH-v7[5678]\..*? \*/.*?#endif\n', '', raw_content, flags=re.DOTALL)
    
    preamble = synthesize_preamble()
    content = apply_dynamic_fixes(content)
    
    final_output = preamble + content
    
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    src_root = Path("./decomp-files/src") 
    decomp_root = Path("./decomp-files")
    
    if not src_root.exists():
        print("[-] Error: Source root not found.")
        return

    print(f"[>] Running Automorph v79.0-AArch64 (Deep Clean Mode)...")
    
    # 1. Execute Header-Level Deep Cleans
    neutralize_bool_header(decomp_root)
    fix_audio_struct_redefinitions(decomp_root)
    
    # 2. Process all C files
    count = 0
    for c_file in src_root.rglob("*.c"):
        if process_file(c_file):
            count += 1
            
    print(f"\n[!] Success: {count} files processed. Struct tags and bool.h neutralized.")

if __name__ == "__main__":
    main()
