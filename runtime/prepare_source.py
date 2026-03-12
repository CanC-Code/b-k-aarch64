#!/usr/bin/env python3
import re
import hashlib
import os
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-AUTOMORPH-ACTIVE-V81.9-STABLE */"

def deep_clean_sdk(decomp_root: Path):
    """
    Harmonizes the SDK headers by removing clashing types and fixing 64-bit issues.
    """
    # 1. Neutralize bool.h
    bool_h = decomp_root / "include" / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#include <stdbool.h>\n", encoding='utf-8')

    # 2. RENAME CLASHING SYSTEM HEADERS
    clashes = ["string.h", "time.h", "math.h", "assert.h"]
    for name in clashes:
        old_path = decomp_root / "include" / name
        new_path = decomp_root / "include" / f"n64_{name}"
        if old_path.exists():
            if new_path.exists(): new_path.unlink()
            old_path.rename(new_path)

    # 3. FIX PRIMITIVES IN n64_types.h
    # We remove the Gfx/Mtx stubs here because we want to use the real ones in gbi.h
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

// Missing Opaque Types (Safe stubs)
#ifndef _ALHEAP_STUB_
#define _ALHEAP_STUB_
typedef struct { u8 dummy[16]; } ALHeap;
#endif

#endif
""", encoding='utf-8')

    # 4. SURGICAL PATCHING OF GBI.H (Fixes Mtx_t and Gfx redefinitions)
    gbi_h = decomp_root / "include/2.0L/PR/gbi.h"
    if gbi_h.exists():
        content = gbi_h.read_text(encoding='utf-8', errors='ignore')
        # Fix the 'long' vs 'int32_t' issue on 64-bit systems
        content = content.replace("typedef long    Mtx_t[4][4];", "typedef int32_t Mtx_t[4][4];")
        # Ensure Vtx is visible to other headers
        if "typedef struct {" in content and "} Vtx;" in content:
            content = content.replace("typedef struct {", "#ifndef _VTX_DEFINED_\n#define _VTX_DEFINED_\ntypedef struct {", 1)
            content = content.replace("} Vtx;", "} Vtx;\n#endif", 1)
        gbi_h.write_text(content, encoding='utf-8')

def apply_source_fixes(content, file_path):
    # Standard Include Renaming
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "time.h"', '#include "n64_time.h"')
    content = content.replace('#include "math.h"', '#include "n64_math.h"')
    
    # Implementation renaming for memory.c
    if "memory.c" in str(file_path):
        content = content.replace("void memcpy(void * dst", "void n64_memcpy(void * _dst")
        content = content.replace("void memmove(void * dst", "void n64_memmove(void * _dst")
        content = content.replace("void memmove(u8* dst", "void n64_memmove(void * _dst")
    
    # 64-bit Pointer Truncation
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
    print("[>] SourceHarmonizer v81.9: Resolving Typedef Redefinitions")
    deep_clean_sdk(decomp_root)
    
    for root in [decomp_root / "src", decomp_root / "include"]:
        for file_path in root.rglob("*.[ch]"):
            process_file(file_path)

if __name__ == "__main__": main()
