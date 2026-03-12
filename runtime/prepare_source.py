#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-v80.3-AUTOMORPH */"

# Global counter to ensure uniqueness across ALL files
GLOBAL_STRUCT_COUNTER = 0

def unique_struct_fix(match):
    """
    Callback for re.sub to provide globally unique tags for anonymous structs.
    """
    global GLOBAL_STRUCT_COUNTER
    GLOBAL_STRUCT_COUNTER += 1
    
    struct_body = match.group(1)
    typename = match.group(2)
    tag = f"_SH_GLOBAL_TAG_{GLOBAL_STRUCT_COUNTER}"
    
    return f"typedef struct {tag} {{{struct_body}}} {typename};"

def deep_clean_sdk(decomp_root: Path):
    """
    Physically repairs legacy SDK headers to work with modern Clang.
    """
    # 1. Neutralize bool.h
    bool_h = decomp_root / "include" / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#include <stdbool.h>\n", encoding='utf-8')
        print("  [FIXED] bool.h redirected to stdbool.h")

    # 2. Fix redefinition patterns in all potential audio/SDK headers
    audio_headers = [
        decomp_root / "include/2.0L/PR/libaudio.h",
        decomp_root / "include/2.0L/PR/n_libaudio.h",
        decomp_root / "include/synthInternals.h"
    ]
    
    for h_path in audio_headers:
        if not h_path.exists():
            continue
            
        content = h_path.read_text(encoding='utf-8', errors='ignore')
        
        # Apply the unique struct tagger globally across all files
        content = re.sub(r'typedef\s+struct\s*\{(.*?)\}\s*(\w+);', unique_struct_fix, content, flags=re.DOTALL)
        
        # Fix specific N64 SDK naming traps
        content = content.replace("struct ALFilter_s", "struct ALFilter")
        content = content.replace("struct ALAuxBus_s", "struct ALAuxBus")
        
        h_path.write_text(content, encoding='utf-8')
        print(f"  [FIXED] {h_path.name} normalized with global tags.")

def synthesize_preamble():
    """
    Standard preamble for modern AArch64/Clang compatibility.
    """
    return f"""{PREAMBLE_MARKER}
#ifndef _SH_DYNAMIC_GUARD_
#define _SH_DYNAMIC_GUARD_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

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

#define _BOOL_H_

#endif
"""

def apply_source_fixes(content):
    # 64-bit Pointer Truncation fixes
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    content = re.sub(r'\(u32\)\s*\((.*?)\)', r'(u32)(uintptr_t)(\1)', content)
    
    clash_patterns = [
        r'struct\s+ALCSPlayer;', r'typedef\s+struct\s+ALCSPlayer\s+ALCSPlayer;',
        r'struct\s+N_ALCSPlayer;', r'typedef\s+struct\s+N_ALCSPlayer\s+N_ALCSPlayer;'
    ]
    for pattern in clash_patterns:
        content = re.sub(pattern, '', content)
        
    return content

def process_file(path):
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    
    # Wipe previous preamble versions
    content = re.sub(r'/\* SH-v.*?\*/.*?#endif\n', '', raw_content, flags=re.DOTALL)
    
    preamble = synthesize_preamble()
    content = apply_source_fixes(content)
    
    final_output = preamble + content
    
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path("./")
    src_root = repo_root / "decomp-files/src"
    decomp_root = repo_root / "decomp-files"

    print(f"[>] SourceHarmonizer v80.3: Global SDK Synchronization")
    
    deep_clean_sdk(decomp_root)
    
    count = 0
    if src_root.exists():
        for c_file in src_root.rglob("*.c"):
            if process_file(c_file):
                count += 1
        print(f"\n[!] Success: {count} source files harmonized.")
    else:
        print(f"[ERROR] Path not found: {src_root}")

if __name__ == "__main__":
    main()
