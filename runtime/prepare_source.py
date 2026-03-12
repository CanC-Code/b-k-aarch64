#!/usr/bin/env python3
import re
import hashlib
import os
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-AUTOMORPH-ACTIVE-V81.3-STABLE */"

def get_content_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:8]

def unique_struct_fix(match):
    struct_body = match.group(1)
    typename = match.group(2)
    tag_id = get_content_hash(struct_body)
    return f"typedef struct _SH_TAG_{tag_id} {{{struct_body}}} {typename};"

def deep_clean_sdk(decomp_root: Path):
    """
    Deletes shadowing headers and force-redirects to system libraries.
    """
    # 1. Neutralize bool.h
    bool_h = decomp_root / "include" / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#include <stdbool.h>\n", encoding='utf-8')

    # 2. DELETE SHADOWING HEADERS (The Nuclear Option)
    # These legacy files cause infinite recursion or 'no member' errors in C++
    shadows = [
        decomp_root / "include" / "string.h",
        decomp_root / "include" / "core1" / "mem.h"
    ]
    for s_path in shadows:
        if s_path.exists():
            s_path.unlink() # Delete the file so the compiler MUST use the system one
            print(f"  [DELETED SHADOW] {s_path.name} removed to prevent C++ collision.")

    # 3. Standard SDK Struct Fixes
    audio_headers = [
        decomp_root / "include/2.0L/PR/libaudio.h",
        decomp_root / "include/2.0L/PR/n_libaudio.h",
        decomp_root / "include/synthInternals.h"
    ]
    for h_path in audio_headers:
        if not h_path.exists(): continue
        content = h_path.read_text(encoding='utf-8', errors='ignore')
        content = re.sub(r'typedef\s+struct\s*\{(.*?)\}\s*(\w+);', unique_struct_fix, content, flags=re.DOTALL)
        content = content.replace("struct ALFilter_s", "struct ALFilter")
        content = content.replace("struct ALAuxBus_s", "struct ALAuxBus")
        h_path.write_text(content, encoding='utf-8')

def synthesize_preamble(file_path):
    # This preamble ensures all standard functions are available in global namespace
    preamble = f"""{PREAMBLE_MARKER}
#ifndef _SH_DYNAMIC_GUARD_
#define _SH_DYNAMIC_GUARD_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>

#ifdef __cplusplus
#include <cstring>
using namespace std;
#endif

#ifndef _SH_PRIMITIVES_
#define _SH_PRIMITIVES_
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
#endif
#ifndef FALSE
#define FALSE false
#endif
#endif

#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif
#define _BOOL_H_
"""
    if "code_1D00.c" in str(file_path):
        preamble += "\nstruct AudioInfo_s; typedef struct AudioInfo_s AudioInfo;\n"
        preamble += "bool audioManager_handleFrameMsg(AudioInfo *info, AudioInfo *prev_info);\n"

    preamble += "#endif\n"
    return preamble

def apply_source_fixes(content):
    # Redirect legacy includes to system brackets
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "core1/mem.h"', '#include <string.h>')
    
    # 64-bit Pointer Truncation
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    content = re.sub(r'\(u32\)\s*\((.*?)\)', r'(u32)(uintptr_t)(\1)', content)
    
    # Signature harmonization
    content = content.replace("bool func_80253400(void)", "int func_80253400(void)")
    return content

def process_file(path, is_header=False):
    # Only process C files for preamble injection
    if path.suffix == ".cpp": return False
    
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    content = re.sub(r'/\* SH-.*?\*/.*?#endif\n', '', raw_content, flags=re.DOTALL)
    fixed_content = apply_source_fixes(content)
    
    final_output = (synthesize_preamble(path) if not is_header else "") + fixed_content
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path("./")
    src_root = repo_root / "decomp-files/src"
    inc_root = repo_root / "decomp-files/include"
    decomp_root = repo_root / "decomp-files"
    
    print("[>] SourceHarmonizer v81.3: Shadow Header Elimination")
    deep_clean_sdk(decomp_root)
    
    count = 0
    for root in [src_root, inc_root]:
        if not root.exists(): continue
        for ext in ["*.c", "*.h"]:
            for file_path in root.rglob(ext):
                if process_file(file_path, is_header=(ext == "*.h")):
                    count += 1
    print(f"[!] Success: {count} project files harmonized.")

if __name__ == "__main__":
    main()
