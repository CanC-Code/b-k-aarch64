#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-v80.2-AUTOMORPH */"

def unique_struct_fix(match):
    """
    Callback for re.sub to provide unique tags for anonymous structs.
    Ensures that typedef struct { ... } Typename; becomes 
    typedef struct _SH_TAG_N { ... } Typename;
    """
    if not hasattr(unique_struct_fix, "counter"):
        unique_struct_fix.counter = 0
    unique_struct_fix.counter += 1
    
    struct_body = match.group(1)
    typename = match.group(2)
    tag = f"_SH_TAG_{unique_struct_fix.counter}"
    
    return f"typedef struct {tag} {{{struct_body}}} {typename};"

def deep_clean_sdk(decomp_root: Path):
    """
    Physically repairs legacy SDK headers to work with modern Clang.
    """
    # 1. Neutralize bool.h to use standard C bools
    bool_h = decomp_root / "include" / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#include <stdbool.h>\n", encoding='utf-8')
        print("  [FIXED] bool.h redirected to stdbool.h")

    # 2. Fix redefinition patterns in audio headers
    audio_headers = [
        decomp_root / "include/2.0L/PR/libaudio.h",
        decomp_root / "include/2.0L/PR/n_libaudio.h",
        decomp_root / "include/synthInternals.h"
    ]
    
    for h_path in audio_headers:
        if not h_path.exists():
            continue
            
        content = h_path.read_text(encoding='utf-8', errors='ignore')
        
        # Reset counter per file to avoid massive tag numbers
        unique_struct_fix.counter = 0
        
        # Use a more robust regex to find typedef struct { body } Typename;
        # This handles nested braces by being non-greedy on the body.
        content = re.sub(r'typedef\s+struct\s*\{(.*?)\}\s*(\w+);', unique_struct_fix, content, flags=re.DOTALL)
        
        # Fix the specific ALFilter/ALAuxBus redefinition traps
        content = content.replace("struct ALFilter_s", "struct ALFilter")
        content = content.replace("struct ALAuxBus_s", "struct ALAuxBus")
        
        h_path.write_text(content, encoding='utf-8')
        print(f"  [FIXED] {h_path.name} normalized with unique tags.")

def synthesize_preamble():
    """
    Defines N64 primitives and guards against legacy type conflicts.
    """
    return f"""{PREAMBLE_MARKER}
#ifndef _SH_DYNAMIC_GUARD_
#define _SH_DYNAMIC_GUARD_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// Force-inject N64 Primitives for modern toolchains
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

#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

// Block legacy N64 bool guards
#define _BOOL_H_

#endif
"""

def apply_source_fixes(content):
    """
    Adjusts source code for 64-bit compatibility and removes SDK-clashing declarations.
    """
    # Fix 64-bit Pointer Truncation (Pointer -> uintptr_t -> u32)
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    content = re.sub(r'\(u32\)\s*\((.*?)\)', r'(u32)(uintptr_t)(\1)', content)
    
    # Remove manual forward declarations that clash with our repaired headers
    clash_patterns = [
        r'struct\s+ALCSPlayer;', r'typedef\s+struct\s+ALCSPlayer\s+ALCSPlayer;',
        r'struct\s+N_ALCSPlayer;', r'typedef\s+struct\s+N_ALCSPlayer\s+N_ALCSPlayer;'
    ]
    for pattern in clash_patterns:
        content = re.sub(pattern, '', content)
        
    return content

def process_file(path):
    """
    Adds the preamble and applies source-level fixes to C files.
    """
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    
    # Remove older version blocks if they exist
    content = re.sub(r'/\* SH-v7[5-9]\..*? \*/.*?#endif\n', '', raw_content, flags=re.DOTALL)
    content = re.sub(r'/\* SH-v80\..*? \*/.*?#endif\n', '', content, flags=re.DOTALL)
    
    preamble = synthesize_preamble()
    content = apply_source_fixes(content)
    
    final_output = preamble + content
    
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    # Adjusted paths to match your CI environment
    repo_root = Path("./")
    src_root = repo_root / "decomp-files/src"
    decomp_root = repo_root / "decomp-files"

    print(f"[>] SourceHarmonizer v80.2: SDK-First Synchronization")
    
    # 1. Repair the SDK headers
    deep_clean_sdk(decomp_root)
    
    # 2. Process all source files
    count = 0
    if src_root.exists():
        for c_file in src_root.rglob("*.c"):
            if process_file(c_file):
                count += 1
        print(f"\n[!] Success: {count} source files harmonized.")
    else:
        print(f"\n[ERROR] Source directory not found at {src_root}")

if __name__ == "__main__":
    main()
