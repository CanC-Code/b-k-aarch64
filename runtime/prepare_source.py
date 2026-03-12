#!/usr/bin/env python3
import re
from pathlib import Path

def setup_headers(decomp_root: Path):
    # 1. Create a bulletproof n64_types.h including 3D types
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

#ifndef TRUE
  #define TRUE true
  #define FALSE false
#endif

// --- Graphics Opaque Types ---
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { u8 d[16]; } Vtx;
typedef struct { u8 d[32]; } LookAt;
typedef struct { u8 d[32]; } Hilite;
typedef struct { u8 d[32]; } Light;
typedef struct { u8 d[64]; } uSprite;
typedef struct { u8 d[64]; } PositionalLight;

// --- Audio Opaque Types ---
typedef uint64_t Acmd;
typedef struct { uint32_t w0; uint32_t w1; } Awords;
typedef struct { uint32_t w0; uint32_t w1; } Apolef;
typedef struct { u8 d[16]; } ALHeap;
typedef struct { u8 d[64]; } Aadpcm;
typedef struct { u8 d[128]; } ADPCM_STATE;
typedef struct { u8 d[128]; } RESAMPLE_STATE;
typedef struct { u8 d[128]; } POLEF_STATE;
typedef struct { u8 d[128]; } ENVMIX_STATE;

#ifndef bcopy
#define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

bool audioManager_handleFrameMsg(void *info, void *prev_info);

#endif
""", encoding='utf-8')

    # 2. Neutralize the recursion in bool.h
    bool_h = decomp_root / "include" / "bool.h"
    bool_h.write_text("#pragma once\n#include <stdbool.h>\n", encoding='utf-8')

    # 3. Force Replace "Toxic" SDK Headers
    toxic_headers = [
        "2.0L/PR/ultratypes.h",
        "2.0L/PR/abi.h",
        "2.0L/PR/mbi.h",
        "2.0L/PR/gbi.h",
        "2.0L/PR/os_libc.h"
    ]
    for h_name in toxic_headers:
        h_path = decomp_root / "include" / h_name
        if h_path.exists():
            h_path.write_text("#include <n64_types.h>\n", encoding='utf-8')

def apply_source_fixes(content):
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "core1/mem.h"', '#include <string.h>')
    # 64-bit Pointer alignment fix
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    return content

def main():
    repo_root = Path("./")
    decomp_root = repo_root / "decomp-files"
    print("[>] SourceHarmonizer v83.1: Hardware Types Expanded")
    
    setup_headers(decomp_root)
    
    for root in [decomp_root / "src", decomp_root / "include"]:
        for file_path in root.rglob("*.[ch]"):
            if file_path.suffix == ".h" and "PR/" in str(file_path): continue
            raw = file_path.read_text(encoding='utf-8', errors='ignore')
            content = re.sub(r'/\* SH-.* \*/\n', '', raw)
            fixed = apply_source_fixes(content)
            file_path.write_text(f"/* SH-AUTOMORPH-V83.1 */\n{fixed}", encoding='utf-8')

if __name__ == "__main__": main()
