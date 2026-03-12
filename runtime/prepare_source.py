#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-AUTOMORPH-ACTIVE-V82.9-FINAL */"

def deep_clean_sdk(decomp_root: Path):
    """
    Completely neutralizes clashing SDK headers and provides ARM64-safe N64 types.
    """
    # 1. Kill the bool.h recursion
    bool_h = decomp_root / "include" / "bool.h"
    bool_h.write_text("#pragma once\n#include <stdbool.h>\n", encoding='utf-8')

    # 2. Re-create n64_types.h with EVERY hardware-specific alignment type
    types_h = decomp_root / "include" / "n64_types.h"
    types_h.write_text("""#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// Standard N64 Primitives
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

// Hardware Alignment Types (ARM64 Neutral)
typedef struct { uint32_t w0; uint32_t w1; } Awords;
typedef struct { uint32_t w0; uint32_t w1; } Apolef;
typedef uint64_t Gfx;
typedef uint64_t Acmd;
typedef int32_t  Mtx_t[4][4];
typedef struct { Mtx_t m; } Mtx;
typedef struct { u8 d[16]; } ALHeap;
typedef struct { u8 d[64]; } Aadpcm;
typedef struct { u8 d[128]; } ADPCM_STATE;

#ifndef bcopy
#define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

bool audioManager_handleFrameMsg(void *info, void *prev_info);

#endif
""", encoding='utf-8')

    # 3. ABSOLUTE NEUTRALIZATION
    # We replace these headers with a single include to our safe types.
    # This prevents the compiler from ever seeing the 'toxic' original code.
    neutral_headers = [
        "2.0L/PR/ultratypes.h",
        "2.0L/PR/abi.h",
        "2.0L/PR/mbi.h",
        "2.0L/PR/os_libc.h"
    ]

    for h_name in neutral_headers:
        h_path = decomp_root / "include" / h_name
        if h_path.exists():
            h_path.write_text("#include <n64_types.h>\n", encoding='utf-8')

    # 4. Patch libaudio.h to skip its conflicting types
    libaudio = decomp_root / "include/2.0L/PR/libaudio.h"
    if libaudio.exists():
        content = libaudio.read_text(encoding='utf-8', errors='ignore')
        # We wrap the whole type-definition block in an 'already defined' guard
        content = "#define _LIB_TYPES_SKIP_\n" + content
        content = content.replace("typedef struct {", "#ifndef _LIB_TYPES_SKIP_\ntypedef struct {")
        content = content.replace("} ALBankFile;", "} ALBankFile;\n#endif")
        libaudio.write_text(content, encoding='utf-8')

def apply_source_fixes(content):
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "core1/mem.h"', '#include <string.h>')
    # 64-bit Pointers
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    return content

def process_file(path):
    if path.suffix == ".cpp": return False
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    content = re.sub(r'/\* SH-.* \*/.*', '', raw_content, flags=re.DOTALL)
    fixed_content = apply_source_fixes(content)
    
    path.write_text(f"{PREAMBLE_MARKER}\n{fixed_content}", encoding='utf-8')
    return True

def main():
    repo_root = Path("./")
    decomp_root = repo_root / "decomp-files"
    print("[>] SourceHarmonizer v82.9: Absolute SDK Neutralization")
    deep_clean_sdk(decomp_root)
    
    for root in [decomp_root / "src", decomp_root / "include"]:
        for file_path in root.rglob("*.[ch]"):
            process_file(file_path)

if __name__ == "__main__": main()
