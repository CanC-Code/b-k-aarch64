#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-AUTOMORPH-ACTIVE-V82.5-STABLE */"

def deep_clean_sdk(decomp_root: Path):
    """
    Physically neutralizes SDK headers to prevent 64-bit type collisions.
    """
    # 1. Master redirect for types
    types_h = decomp_root / "include" / "n64_types.h"
    types_h.write_text("""#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

typedef uint8_t u8;   typedef int8_t s8;
typedef uint16_t u16; typedef int16_t s16;
typedef uint32_t u32; typedef int32_t s32;
typedef uint64_t u64; typedef int64_t s64;
typedef float f32;    typedef double f64;
typedef volatile uint32_t vu32; typedef volatile int32_t vs32;
typedef volatile uint16_t vu16; typedef volatile int16_t vs16;
typedef volatile uint8_t  vu8;  typedef volatile int8_t  vs8;

#ifndef TRUE
  #define TRUE true
  #define FALSE false
#endif

// Audio Stubs
typedef struct { u8 dummy[16]; } ALHeap;
typedef struct { u8 dummy[64]; } Aadpcm;
typedef struct { u8 dummy[64]; } ADPCM_STATE;

#ifndef bcopy
#define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

#endif
""", encoding='utf-8')

    # 2. Neutralize ultratypes.h (The source of 'unsigned long' conflicts)
    u_types = decomp_root / "include/2.0L/PR/ultratypes.h"
    if u_types.exists():
        u_types.write_text("#include <n64_types.h>\n", encoding='utf-8')

    # 3. Neutralize other clashing headers
    neutralize_list = [
        "string.h", "time.h", "math.h", "assert.h", "bool.h"
    ]
    for name in neutralize_list:
        p = decomp_root / "include" / name
        if p.exists():
            # Replace with system includes
            p.write_text(f"#include <{name}>\n", encoding='utf-8')

    # 4. Patch os_libc.h to remove conflicting bcopy declaration
    os_libc = decomp_root / "include/2.0L/PR/os_libc.h"
    if os_libc.exists():
        content = os_libc.read_text(encoding='utf-8', errors='ignore')
        content = content.replace("extern void     bcopy", "// extern void bcopy")
        os_libc.write_text(content, encoding='utf-8')

def synthesize_preamble():
    # Fixed: Using actual newlines instead of literal \n
    return f"{PREAMBLE_MARKER}\n"

def apply_source_fixes(content):
    # Header redirects
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "core1/mem.h"', '#include <string.h>')
    
    # 64-bit Pointer Truncation Repair
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    return content

def process_file(path):
    if path.suffix == ".cpp": return False
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    
    # Clean old content and apply fixes
    content = re.sub(r'/\* SH-.* \*/.*', '', raw_content, flags=re.DOTALL)
    fixed_content = apply_source_fixes(content)
    
    final_output = synthesize_preamble() + fixed_content
    
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path("./")
    decomp_root = repo_root / "decomp-files"
    print("[>] SourceHarmonizer v82.5: Fixing String Literal Bug")
    deep_clean_sdk(decomp_root)
    
    for root in [decomp_root / "src", decomp_root / "include"]:
        for file_path in root.rglob("*.[ch]"):
            process_file(file_path)

if __name__ == "__main__": main()
