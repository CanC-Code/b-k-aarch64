#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-v76.5-AUTOMORPH */"

def get_dangling_references(content):
    """
    Identifies N64-era legacy types that lack definitions.
    Scans for pointers in prototypes, extern declarations, and casts.
    """
    # Pattern 1: Detects types in function pointers/prototypes: extern void func(TypeName *ptr);
    proto_type = r'(?:\w+\s+)+\w+\s*\([^)]*?\b([A-Z][a-zA-Z0-9_]+|N_[A-Z]\w+)\s*\*'
    
    # Pattern 2: Detects types in extern variable declarations: extern TypeName global_var;
    extern_type = r'extern\s+([A-Z][a-zA-Z0-9_]+|N_[A-Z]\w+)\s+\w+;'
    
    # Pattern 3: Detects types in explicit casts: (TypeName *)var
    cast_type = r'\(([A-Z][a-zA-Z0-9_]+|N_[A-Z]\w+)\s*\*\)'

    found = set()
    for pattern in [proto_type, extern_type, cast_type]:
        found.update(re.findall(pattern, content))
    
    # Block standard C types and types we've already defined as primitives
    standard_ignores = {
        'FILE', 'DIR', 'size_t', 'uintptr_t', 'intptr_t', 'u8', 'u16', 'u32', 'u64',
        's8', 's16', 's32', 's64', 'f32', 'f64', 'Mtx', 'Vtx', 'Gfx', 'u_char'
    }
    return found - standard_ignores

def synthesize_preamble(content):
    dangling = get_dangling_references(content)
    
    stubs = []
    for t in sorted(dangling):
        # Using a struct-tag approach ensures '->' and '.' operators don't crash the compiler
        # but the macro guard prevents "redefinition" errors if the actual SDK header is included.
        guard = f"_SH_GUARD_{t}"
        stubs.append(f"#ifndef {guard}")
        stubs.append(f"#define {guard}")
        stubs.append(f"typedef struct {t} {{ uint8_t opaque[1]; }} {t};")
        stubs.append(f"#endif")

    stubs_block = "\n".join(stubs)
    
    return f"""{PREAMBLE_MARKER}
#ifndef _SH_DYNAMIC_GUARD_
#define _SH_DYNAMIC_GUARD_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// Standard N64/IDO Primitive Mapping
#ifndef _ULTRATYPES_H_
typedef uint8_t u8; typedef int8_t s8;
typedef uint16_t u16; typedef int16_t s16;
typedef uint32_t u32; typedef int32_t s32;
typedef uint64_t u64; typedef int64_t s64;
typedef float f32; typedef double f64;
#define _ULTRATYPES_H_
#endif

// Dynamically Discovered Legacy Types (Virtualized)
{stubs_block}

// Global Android/Clang Fixes
#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

#endif
"""

def apply_64bit_fix(content):
    """
    Prevents pointer truncation on AArch64.
    Finds (u32) casts of addresses and inserts (uintptr_t) mid-step.
    """
    # Fix (u32)&var or (u32)ptr_var
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    # Fix complex member access casts: (u32)obj->member
    content = re.sub(r'\(u32\)\s*\((.*?)\)', r'(u32)(uintptr_t)(\1)', content)
    return content

def process_file(path):
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    
    # 1. Clean previous version markers (all versions of SH-v75 or SH-v76)
    content = re.sub(r'/\* SH-v7[56]\..*? \*/.*?#endif\n', '', raw_content, flags=re.DOTALL)
    
    # 2. Dynamic Discovery
    preamble = synthesize_preamble(content)
    
    # 3. 64-bit Harmonization
    content = apply_64bit_fix(content)
    
    final_output = preamble + content
    
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    # Targets the local project source
    src_root = Path("./decomp-files/src") 
    if not src_root.exists():
        print("[-] Error: Path ./decomp-files/src not found.")
        return

    print(f"[>] Harmonizing project: {src_root.resolve()}")
    
    count = 0
    for c_file in src_root.rglob("*.c"):
        if process_file(c_file):
            print(f"  [+] Automorphing: {c_file.relative_to(src_root)}")
            count += 1
            
    print(f"\n[!] Success: {count} files harmonized for 64-bit Android.")

if __name__ == "__main__":
    main()
