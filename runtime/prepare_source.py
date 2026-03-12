#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-AUTOMORPH-ACTIVE-V82.6-FINAL */"

def deep_clean_sdk(decomp_root: Path):
    """
    Final surgical cleanup to allow N64 audio types to coexist with modern C.
    """
    # 1. Kill the bool.h recursion loop
    bool_h = decomp_root / "include" / "bool.h"
    bool_h.write_text("#pragma once\n#include <stdbool.h>\n", encoding='utf-8')

    # 2. Master redirect for types (Using Macros to block redefinitions)
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

#ifndef TRUE
  #define TRUE true
  #define FALSE false
#endif

// We define these as macros to 'snatch' the name from abi.h/libaudio.h
#define ALHeap void
#define Aadpcm void
#define ADPCM_STATE void
#define ALMicroTime int32_t

#ifndef bcopy
#define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

// Generic prototype for the manager
bool audioManager_handleFrameMsg(void *info, void *prev_info);

#endif
""", encoding='utf-8')

    # 3. Neutralize ultratypes.h
    u_types = decomp_root / "include/2.0L/PR/ultratypes.h"
    if u_types.exists():
        u_types.write_text("#include <n64_types.h>\n", encoding='utf-8')

    # 4. Patch libaudio.h and abi.h to respect our name-snatching
    for header_name in ["2.0L/PR/libaudio.h", "2.0L/PR/abi.h"]:
        h_path = decomp_root / "include" / header_name
        if h_path.exists():
            content = h_path.read_text(encoding='utf-8', errors='ignore')
            # Wrap their typedefs in checks
            content = content.replace("} ALHeap;", "#ifndef ALHeap\n} ALHeap;\n#endif")
            content = content.replace("} Aadpcm;", "#ifndef Aadpcm\n} Aadpcm;\n#endif")
            content = content.replace("typedef short ADPCM_STATE", "#ifndef ADPCM_STATE\ntypedef short ADPCM_STATE")
            h_path.write_text(content, encoding='utf-8')

def apply_source_fixes(content):
    # Header redirects
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "core1/mem.h"', '#include <string.h>')
    # 64-bit Pointer Truncation Repair
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    return content

def process_file(path):
    if path.suffix == ".cpp": return False
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    content = re.sub(r'/\* SH-.* \*/.*', '', raw_content, flags=re.DOTALL)
    fixed_content = apply_source_fixes(content)
    final_output = f"{PREAMBLE_MARKER}\n" + fixed_content
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path("./")
    decomp_root = repo_root / "decomp-files"
    print("[>] SourceHarmonizer v82.6: Name-Snatching Active")
    deep_clean_sdk(decomp_root)
    for root in [decomp_root / "src", decomp_root / "include"]:
        for file_path in root.rglob("*.[ch]"):
            process_file(file_path)

if __name__ == "__main__": main()
