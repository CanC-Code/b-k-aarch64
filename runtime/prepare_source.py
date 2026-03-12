#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-AUTOMORPH-ACTIVE-V82.7-STABLE */"

def deep_clean_sdk(decomp_root: Path):
    """
    Surgically cleans the SDK to allow 32-bit N64 types to coexist with 64-bit ARM.
    """
    # 1. Kill the bool.h recursion loop
    bool_h = decomp_root / "include" / "bool.h"
    bool_h.write_text("#pragma once\n#include <stdbool.h>\n", encoding='utf-8')

    # 2. Establish n64_types.h (The Proxy Bridge)
    types_h = decomp_root / "include" / "n64_types.h"
    types_h.write_text(f"""#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// Standard N64 Primitives
typedef uint8_t u8;   typedef int8_t s8;
typedef uint16_t u16; typedef int16_t s16;
typedef uint32_t u32; typedef int32_t s32;
typedef uint64_t u64; typedef int64_t s64;
typedef float f32;    typedef double f64;
typedef volatile uint32_t vu32; typedef volatile int32_t vs32;

#ifndef TRUE
  #define TRUE true
  #define FALSE false
#endif

// Alignment types for Audio Command Lists (Fixes 'Awords' error)
typedef struct {{ uint32_t w0; uint32_t w1; }} Awords;

// Proxy Structs for Audio Types (Prevents 'typedef redefinition' errors)
typedef struct {{ u8 d[16]; }} _SH_ALHeap;
typedef struct {{ u8 d[64]; }} _SH_Aadpcm;
typedef struct {{ u8 d[64]; }} _SH_ADPCM_STATE;

#define ALHeap _SH_ALHeap
#define Aadpcm _SH_Aadpcm
#define ADPCM_STATE _SH_ADPCM_STATE

#ifndef bcopy
#define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

// Forward Declaration for game logic
bool audioManager_handleFrameMsg(void *info, void *prev_info);

#endif
""", encoding='utf-8')

    # 3. Aggressive SDK Neutralization (abi.h and libaudio.h)
    # We physically comment out the typedef lines to stop the compiler from seeing them
    for header_name in ["2.0L/PR/libaudio.h", "2.0L/PR/abi.h", "2.0L/PR/ultratypes.h"]:
        h_path = decomp_root / "include" / header_name
        if h_path.exists():
            content = h_path.read_text(encoding='utf-8', errors='ignore')
            # Comment out the specific offending typedef lines
            content = content.replace("typedef struct {", "/* [SH] typedef struct {")
            content = content.replace("} ALHeap;", "} ALHeap; */")
            content = content.replace("} Aadpcm;", "} Aadpcm; */")
            content = content.replace("typedef short ADPCM_STATE", "// [SH] typedef short ADPCM_STATE")
            
            # Special case for ultratypes.h: it must be a redirect only
            if "ultratypes.h" in header_name:
                content = "#include <n64_types.h>\n"
                
            h_path.write_text(content, encoding='utf-8')

def apply_source_fixes(content):
    # Header redirects to system
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "core1/mem.h"', '#include <string.h>')
    
    # 64-bit Pointer Truncation Repair (The uintptr_t cast)
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    return content

def process_file(path):
    if path.suffix == ".cpp": return False
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    
    # Clean and apply fixes
    content = re.sub(r'/\* SH-.* \*/.*', '', raw_content, flags=re.DOTALL)
    fixed_content = apply_source_fixes(content)
    
    final_output = f"{PREAMBLE_MARKER}\n" + fixed_content
    
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path("./")
    decomp_root = repo_root / "decomp-files"
    print("[>] SourceHarmonizer v82.7: Opaque Proxies Active")
    deep_clean_sdk(decomp_root)
    
    for root in [decomp_root / "src", decomp_root / "include"]:
        for file_path in root.rglob("*.[ch]"):
            process_file(file_path)

if __name__ == "__main__": main()
