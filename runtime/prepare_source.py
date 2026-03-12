#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-v76.6-AUTOMORPH */"

def get_dangling_references(content):
    """
    Scans for N64-era types that cause 'unknown type' errors in Clang.
    """
    # Pattern 1: Detects types in prototypes: extern void func(TypeName *ptr);
    proto_type = r'(?:\w+\s+)+\w+\s*\([^)]*?\b([A-Z][a-zA-Z0-9_]+|N_[A-Z]\w+)\s*\*'
    
    # Pattern 2: Detects types in extern variable declarations
    extern_type = r'extern\s+([A-Z][a-zA-Z0-9_]+|N_[A-Z]\w+)\s+\w+;'
    
    # Pattern 3: Detects types in explicit casts
    cast_type = r'\(([A-Z][a-zA-Z0-9_]+|N_[A-Z]\w+)\s*\*\)'

    found = set()
    for pattern in [proto_type, extern_type, cast_type]:
        found.update(re.findall(pattern, content))
    
    # Block standard C types and primitives already defined in our template
    standard_ignores = {
        'FILE', 'DIR', 'size_t', 'uintptr_t', 'intptr_t', 'u8', 'u16', 'u32', 'u64',
        's8', 's16', 's32', 's64', 'f32', 'f64', 'Mtx', 'Vtx', 'Gfx', 'u_char', 'void'
    }
    return found - standard_ignores

def synthesize_preamble(content):
    dangling = get_dangling_references(content)
    
    stubs = []
    for t in sorted(dangling):
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

// Force-inject N64 Primitives (Fixes 'unknown type name' errors)
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

// Guard against SDK redefinitions while providing necessary types
{stubs_block}

#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

#endif
"""

def apply_64bit_fix(content):
    """
    Targets pointer-to-u32 conversion errors by injecting uintptr_t.
    """
    # Fix: (u32)&variable or (u32)ptr
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    # Fix: complex parenthetical casts
    content = re.sub(r'\(u32\)\s*\((.*?)\)', r'(u32)(uintptr_t)(\1)', content)
    return content

def process_file(path):
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    
    # Remove all previous Harmonizer versions (v75.x, v76.x)
    content = re.sub(r'/\* SH-v7[56]\..*? \*/.*?#endif\n', '', raw_content, flags=re.DOTALL)
    
    # Dynamically generate the new header
    preamble = synthesize_preamble(content)
    content = apply_64bit_fix(content)
    
    final_output = preamble + content
    
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    src_root = Path("./decomp-files/src") 
    if not src_root.exists():
        print("[-] Source path not found.")
        return

    print(f"[>] Running Automorph v76.6...")
    
    count = 0
    for c_file in src_root.rglob("*.c"):
        if process_file(c_file):
            print(f"  [+] Synced: {c_file.name}")
            count += 1
            
    print(f"\n[!] Success: Harmonized {count} files for AArch64.")

if __name__ == "__main__":
    main()
