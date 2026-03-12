#!/usr/bin/env python3
import re
import hashlib
import os
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-AUTOMORPH-ACTIVE-V81.8-STABLE */"

def deep_clean_sdk(decomp_root: Path):
    """
    Renames clashing headers and establishes the N64 hardware abstraction layer.
    """
    # 1. Neutralize bool.h
    bool_h = decomp_root / "include" / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#include <stdbool.h>\n", encoding='utf-8')

    # 2. RENAME CLASHING HEADERS
    clashes = ["string.h", "time.h", "math.h", "assert.h"]
    for name in clashes:
        old_path = decomp_root / "include" / name
        new_path = decomp_root / "include" / f"n64_{name}"
        if old_path.exists():
            if new_path.exists(): new_path.unlink()
            old_path.rename(new_path)

    # 3. CREATE MASTER N64 TYPES (Fixes Gfx, Mtx, Acmd errors)
    types_h = decomp_root / "include" / "n64_types.h"
    types_h.write_text("""#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stdbool.h>

// Standard Primitives
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

// Opaque N64 Hardware Types (Stubs to satisfy headers)
typedef uint64_t Gfx;
typedef uint64_t Acmd;
typedef int32_t  Mtx_t[4][4];
typedef struct { Mtx_t m; } Mtx;
typedef struct { u8 dummy; } LookAt;
typedef struct { u8 dummy; } Hilite;
typedef struct { u8 dummy; } ADPCM_STATE;

#endif
""", encoding='utf-8')

    # 4. Patch ultra64.h to prevent recursive loops
    u64_h = decomp_root / "include/2.0L/ultra64.h"
    if u64_h.exists():
        u64_h.write_text("#include <n64_types.h>\n#include <PR/os.h>\n", encoding='utf-8')

def apply_source_fixes(content, file_path):
    # Update includes to renamed headers
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "time.h"', '#include "n64_time.h"')
    content = content.replace('#include "math.h"', '#include "n64_math.h"')
    
    # Signature repair for memory.c
    if "memory.c" in str(file_path):
        content = content.replace("void memcpy(void * dst", "void n64_memcpy(void * _dst")
        content = content.replace("void memmove(u8* dst", "void n64_memmove(void * _dst")
    
    # Pointer Truncation
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    return content

def process_file(path):
    if path.suffix == ".cpp": return False
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    content = re.sub(r'/\* SH-.*?\*/.*?#endif\n', '', raw_content, flags=re.DOTALL)
    fixed_content = apply_source_fixes(content, path)
    if fixed_content != raw_content:
        path.write_text(fixed_content, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path("./")
    decomp_root = repo_root / "decomp-files"
    print("[>] SourceHarmonizer v81.8: Injecting Opaque Types")
    deep_clean_sdk(decomp_root)
    
    count = 0
    for root in [decomp_root / "src", decomp_root / "include"]:
        for file_path in root.rglob("*.[ch]"):
            if process_file(file_path): count += 1
    print(f"[!] Success: {count} project files harmonized.")

if __name__ == "__main__": main()
