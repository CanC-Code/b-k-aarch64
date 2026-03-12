#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-v77.0-AUTOMORPH */"

def get_dangling_references(content):
    """
    Scans for N64 types that lack definitions in the current file context.
    """
    # Pattern 1: Function pointers/arguments: void func(TypeName *ptr)
    proto_type = r'(?:\w+\s+)+\w+\s*\([^)]*?\b([A-Z][a-zA-Z0-9_]+|N_[A-Z]\w+)\s*\*'
    # Pattern 2: Extern variable declarations: extern TypeName name;
    extern_type = r'extern\s+([A-Z][a-zA-Z0-9_]+|N_[A-Z]\w+)\s+\w+;'
    # Pattern 3: Explicit pointer casts: (TypeName *)var
    cast_type = r'\(([A-Z][a-zA-Z0-9_]+|N_[A-Z]\w+)\s*\*\)'

    found = set()
    for pattern in [proto_type, extern_type, cast_type]:
        found.update(re.findall(pattern, content))
    
    standard_ignores = {
        'FILE', 'DIR', 'size_t', 'uintptr_t', 'intptr_t', 'u8', 'u16', 'u32', 'u64',
        's8', 's16', 's32', 's64', 'f32', 'f64', 'Mtx', 'Vtx', 'Gfx', 'u_char', 'void'
    }
    return found - standard_ignores

def synthesize_preamble(content):
    dangling = get_dangling_references(content)
    
    forward_decls = []
    for t in sorted(dangling):
        # FIX: We use 'struct Name' forward declarations instead of typedefs.
        # This allows the 'real' header to define the full struct later 
        # without a 'redefinition' error.
        guard = f"_SH_GUARD_{t}"
        forward_decls.append(f"#ifndef {guard}")
        forward_decls.append(f"#define {guard}")
        forward_decls.append(f"struct {t};")
        forward_decls.append(f"typedef struct {t} {t};")
        forward_decls.append(f"#endif")

    decls_block = "\n".join(forward_decls)
    
    return f"""{PREAMBLE_MARKER}
#ifndef _SH_DYNAMIC_GUARD_
#define _SH_DYNAMIC_GUARD_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// Legacy bool neutralization (Prevents conflict with stdbool.h)
#define _BOOL_H_ 
#define _LIB_BOOL_H_

// Force-inject N64 Primitives
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

// Forward declarations for Discovered Types
{decls_block}

#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

#endif
"""

def apply_dynamic_fixes(content):
    """
    Handles pointer truncation and logic fixes for AArch64.
    """
    # 64-bit Pointer Truncation Fixes
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    content = re.sub(r'\(u32\)\s*\((.*?)\)', r'(u32)(uintptr_t)(\1)', content)
    
    # Neutralize inline legacy bool typedefs that might be inside .c files
    content = re.sub(r'^typedef\s+int\s+bool;', r'// typedef int bool; // Handled by stdbool', content, flags=re.M)
    
    return content

def process_file(path):
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    
    # Clean old Harmonizer versions
    content = re.sub(r'/\* SH-v7[567]\..*? \*/.*?#endif\n', '', raw_content, flags=re.DOTALL)
    
    preamble = synthesize_preamble(content)
    content = apply_dynamic_fixes(content)
    
    final_output = preamble + content
    
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    src_root = Path("./decomp-files/src") 
    if not src_root.exists():
        print("[-] Error: Source root not found.")
        return

    print(f"[>] Running Automorph v77.0-AArch64...")
    count = 0
    for c_file in src_root.rglob("*.c"):
        if process_file(c_file):
            print(f"  [+] Harmonized: {c_file.name}")
            count += 1
            
    print(f"\n[!] Success: {count} files processed. 'Redefinition' and 'Bool' conflicts resolved.")

if __name__ == "__main__":
    main()
