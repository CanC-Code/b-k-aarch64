#!/usr/bin/env python3
import re
import hashlib
import os
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-AUTOMORPH-ACTIVE-V81.7-RENAME */"

def deep_clean_sdk(decomp_root: Path):
    """
    Renames clashing headers to prevent Android System headers from loading them.
    """
    # 1. Neutralize bool.h
    bool_h = decomp_root / "include" / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#include <stdbool.h>\n", encoding='utf-8')

    # 2. RENAME CLASHING HEADERS
    # These legacy filenames are identical to standard C headers.
    clashes = ["string.h", "time.h", "math.h", "assert.h"]
    for name in clashes:
        old_path = decomp_root / "include" / name
        new_path = decomp_root / "include" / f"n64_{name}"
        if old_path.exists():
            if new_path.exists(): new_path.unlink()
            old_path.rename(new_path)
            print(f"  [RENAMED] {name} -> n64_{name}")

    # 3. Create a master types header for force-inclusion
    types_h = decomp_root / "include" / "n64_types.h"
    types_h.write_text("""#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
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
#endif
""", encoding='utf-8')

def apply_source_fixes(content):
    # Update includes to point to renamed headers
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "time.h"', '#include "n64_time.h"')
    content = content.replace('#include "math.h"', '#include "n64_math.h"')
    content = content.replace('#include "assert.h"', '#include "n64_assert.h"')
    
    # Implementation renaming for memory.c
    content = content.replace("void memcpy(void * dst", "void n64_memcpy(void * _dst")
    content = content.replace("void memmove(u8* dst", "void n64_memmove(void * _dst")
    
    # 64-bit Pointer Truncation
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    return content

def process_file(path):
    if path.suffix == ".cpp": return False
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    content = re.sub(r'/\* SH-.*?\*/.*?#endif\n', '', raw_content, flags=re.DOTALL)
    fixed_content = apply_source_fixes(content)
    
    if fixed_content != raw_content:
        path.write_text(fixed_content, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path("./")
    decomp_root = repo_root / "decomp-files"
    print("[>] SourceHarmonizer v81.7: Fixing Header Pollution")
    deep_clean_sdk(decomp_root)
    
    count = 0
    for root in [decomp_root / "src", decomp_root / "include"]:
        for file_path in root.rglob("*.[ch]"):
            if process_file(file_path): count += 1
    print(f"[!] Success: {count} project files harmonized.")

if __name__ == "__main__": main()
