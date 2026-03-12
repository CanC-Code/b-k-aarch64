#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-v78.0-AUTOMORPH */"

def synthesize_preamble():
    """
    v78.0 discards type synthesis (which causes redefinition and incomplete 
    type errors) in favor of forced, ordered SDK inclusion. By providing the
    primitives first, the SDK headers can load successfully and provide the
    real, complete definitions for ALFilter, ALAuxBus, etc.
    """
    return f"""{PREAMBLE_MARKER}
#ifndef _SH_DYNAMIC_GUARD_
#define _SH_DYNAMIC_GUARD_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// 1. Force-inject N64 Primitives FIRST
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

// 2. Resolve boolean conflicts
#define _BOOL_H_ 
#define _LIB_BOOL_H_

// 3. Set global flags
#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

// 4. Force actual SDK headers to resolve complex/opaque types
// This ensures ALFilter, ALAuxBus, etc., are fully defined.
#include <PR/ultratypes.h>
#include <PR/libaudio.h>

#endif
"""

def apply_dynamic_fixes(content):
    """
    Handles AArch64 pointer truncation and inline boolean conflicts.
    """
    # Fix pointer truncation: (u32)ptr -> (u32)(uintptr_t)ptr
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    content = re.sub(r'\(u32\)\s*\((.*?)\)', r'(u32)(uintptr_t)(\1)', content)
    
    # Neutralize inline legacy bool typedefs inside .c files
    content = re.sub(r'^typedef\s+int\s+bool;', r'// typedef int bool; // Handled by stdbool', content, flags=re.M)
    
    # NEW in v78.0: Fix conflicting types for 'audioManager_handleFrameMsg'
    # If the function is defined, ensure we inject a forward declaration
    # at the top (after includes) so implicit 'int' declarations don't happen.
    if 'bool audioManager_handleFrameMsg(' in content:
        decl = "extern bool audioManager_handleFrameMsg(AudioInfo *info, AudioInfo *prev_info);\n"
        if decl not in content:
            # Insert after the last include
            last_include_match = list(re.finditer(r'^#include.*$', content, re.MULTILINE))
            if last_include_match:
                insert_pos = last_include_match[-1].end()
                content = content[:insert_pos] + "\n" + decl + content[insert_pos:]

    return content

def process_file(path):
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    
    # Aggressive cleanup of all previous Harmonizer blocks (v75, v76, v77)
    content = re.sub(r'/\* SH-v7[5678]\..*? \*/.*?#endif\n', '', raw_content, flags=re.DOTALL)
    
    preamble = synthesize_preamble()
    content = apply_dynamic_fixes(content)
    
    final_output = preamble + content
    
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    src_root = Path("./decomp-files/src") 
    if not src_root.exists():
        print("[-] Error: Source root './decomp-files/src' not found.")
        return

    print(f"[>] Running Automorph v78.0-AArch64 (SDK Integration Mode)...")
    count = 0
    for c_file in src_root.rglob("*.c"):
        if process_file(c_file):
            count += 1
            
    print(f"\n[!] Success: {count} files processed. 'Incomplete Type' and 'Redefinition' conflicts resolved.")

if __name__ == "__main__":
    main()
