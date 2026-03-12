#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-AUTOMORPH-ACTIVE-V82.3-STABLE */"

def deep_clean_sdk(decomp_root: Path):
    """SDK Sanitation: Removing header collisions."""
    # 1. Neutralize bool.h
    bool_h = decomp_root / "include" / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#include <stdbool.h>\n", encoding='utf-8')

    # 2. DELETE CLASHING HEADERS
    death_list = [
        decomp_root / "include/string.h",
        decomp_root / "include/time.h",
        decomp_root / "include/math.h",
        decomp_root / "include/assert.h",
        decomp_root / "include/core1/mem.h"
    ]
    for path in death_list:
        if path.exists(): path.unlink()

    # 3. CLEAN n64_types.h (Establish base types)
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

#ifndef TRUE
  #define TRUE true
  #define FALSE false
#endif

#ifndef _ALHEAP_H_
#define _ALHEAP_H_
typedef struct { u8 dummy[16]; } ALHeap;
#endif

#endif
""", encoding='utf-8')

def synthesize_preamble(file_path):
    preamble = f"""{PREAMBLE_MARKER}
#ifndef _SH_LOCAL_GUARD_
#define _SH_LOCAL_GUARD_
#include <string.h>

// Built-in Redirects
#ifndef bcopy
#define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

// Forward Declarations for code_1D00.c
#ifdef _LANGUAGE_C
struct AudioInfo_s; 
typedef struct AudioInfo_s AudioInfo;
bool audioManager_handleFrameMsg(AudioInfo *info, AudioInfo *prev_info);
#endif

#endif
"""
    return preamble

def apply_source_fixes(content, file_path):
    # Fix implementations in memory.c if it still exists (though we excluded it in CMake)
    if "memory.c" in str(file_path):
        content = content.replace("void memcpy(void * dst", "void n64_memcpy(void * _dst")
    
    # Header redirects
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "core1/mem.h"', '#include <string.h>')
    
    # 64-bit Pointer Truncation Repair
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\\1', content)
    return content

def process_file(path):
    if path.suffix == ".cpp": return False
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    
    # Clean and Fix
    content = re.sub(r'/\\* SH-.*\\*/.*?#endif\\n', '', raw_content, flags=re.DOTALL)
    fixed_content = apply_source_fixes(content, path)
    
    # Inject Preamble
    final_output = synthesize_preamble(path) + fixed_content
    
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path("./")
    decomp_root = repo_root / "decomp-files"
    print("[>] SourceHarmonizer v82.3: Audio Manager Prototype Fix")
    deep_clean_sdk(decomp_root)
    
    for root in [decomp_root / "src", decomp_root / "include"]:
        for file_path in root.rglob("*.[ch]"):
            process_file(file_path)

if __name__ == "__main__": main()
