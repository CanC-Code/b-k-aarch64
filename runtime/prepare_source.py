#!/usr/bin/env python3
import re
import hashlib
import os
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-AUTOMORPH-ACTIVE-V82.0-STABLE */"

def deep_clean_sdk(decomp_root: Path):
    """
    Final sanitation of the include directory to stop redefinition errors.
    """
    # 1. Neutralize bool.h
    bool_h = decomp_root / "include" / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#include <stdbool.h>\n", encoding='utf-8')

    # 2. DELETE CONFLICTING HEADERS (Instead of renaming, we force system use)
    # core1/mem.h and string.h are the primary causes of the 'overloadable' error
    death_list = [
        decomp_root / "include/string.h",
        decomp_root / "include/time.h",
        decomp_root / "include/math.h",
        decomp_root / "include/assert.h",
        decomp_root / "include/core1/mem.h"
    ]
    for path in death_list:
        if path.exists():
            path.unlink()
            print(f"  [REMOVED] {path.relative_to(decomp_root)} to prevent collision.")

    # 3. FIX n64_types.h (Stronger guards)
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

// Guard ALHeap to prevent redefinition in libaudio.h
#ifndef _ALHEAP_H_
#define _ALHEAP_H_
typedef struct { u8 dummy[16]; } ALHeap;
#endif

// Redirect legacy memory calls
#define memcpy n64_memcpy
#define memmove n64_memmove
#define bcopy(src, dst, n) n64_memmove(dst, src, n)

#endif
""", encoding='utf-8')

def apply_source_fixes(content, file_path):
    # Remove includes of deleted headers
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "core1/mem.h"', '#include <string.h>')
    content = content.replace('#include "time.h"', '#include <time.h>')
    content = content.replace('#include "math.h"', '#include <math.h>')
    
    # Implementation renaming for memory.c
    if "memory.c" in str(file_path):
        content = content.replace("void memcpy(void * dst", "void n64_memcpy(void * _dst")
        content = content.replace("void memmove(u8* dst", "void n64_memmove(void * _dst")
        content = content.replace("void memmove(void * dst", "void n64_memmove(void * _dst")

    # Fix 64-bit Pointer Truncation
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    return content

def process_file(path):
    if path.suffix == ".cpp": return False
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    # Strip old preambles
    content = re.sub(r'/\* SH-.*?\*/.*?#endif\n', '', raw_content, flags=re.DOTALL)
    fixed_content = apply_source_fixes(content, path)
    
    if fixed_content != raw_content:
        path.write_text(fixed_content, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path("./")
    decomp_root = repo_root / "decomp-files"
    print("[>] SourceHarmonizer v82.0: Finalizing Path Sanitation")
    deep_clean_sdk(decomp_root)
    
    count = 0
    for root in [decomp_root / "src", decomp_root / "include"]:
        for file_path in root.rglob("*.[ch]"):
            if process_file(file_path): count += 1
    print(f"[!] Success: {count} project files harmonized.")

if __name__ == "__main__": main()
