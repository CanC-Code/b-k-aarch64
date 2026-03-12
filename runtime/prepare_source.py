#!/usr/bin/env python3
import re
from pathlib import Path

def setup_headers(decomp_root: Path):
    # 1. Create n64_types.h with Snatch Guards
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

// SNATCH GUARDS: These prevent libaudio.h and gu.h from redefining these
#define _ALHEAP_H_
#define _GU_H_
#define _POSITIONAL_LIGHT_H_

typedef struct { uint32_t w0; uint32_t w1; } Awords;
typedef struct { uint32_t w0; uint32_t w1; } Apolef;
typedef uint64_t Gfx;
typedef uint64_t Acmd;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { u8 d[16]; } Vtx;
typedef struct { u8 d[32]; } LookAt;
typedef struct { u8 d[32]; } Hilite;
typedef struct { u8 d[32]; } Light;
typedef struct { u8 d[64]; } uSprite;

// Define these strictly once here
typedef struct { u8 d[16]; } ALHeap;
typedef struct { u8 d[64]; } PositionalLight;
typedef struct { u8 d[64]; } Aadpcm;
typedef struct { u8 d[128]; } ADPCM_STATE;

#ifndef bcopy
#define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

#endif
""", encoding='utf-8')

    # 2. Precision Strike on libaudio.h and gu.h
    # We wrap the original definitions in #ifndef blocks so they don't collide
    for h_name in ["2.0L/PR/libaudio.h", "2.0L/PR/gu.h"]:
        h_path = decomp_root / "include" / h_name
        if h_path.exists():
            content = h_path.read_text(encoding='utf-8', errors='ignore')
            
            # Hide the ALHeap definition
            content = content.replace("typedef struct {", "#ifndef _AL_HIDDEN_\ntypedef struct {", 1)
            content = content.replace("} ALHeap;", "} ALHeap;\n#endif", 1)
            
            # Hide the PositionalLight definition in gu.h
            if "gu.h" in h_name:
                content = content.replace("typedef struct {", "#ifndef _GU_HIDDEN_\ntypedef struct {", 1)
                content = content.replace("} PositionalLight;", "} PositionalLight;\n#endif", 1)
            
            h_path.write_text(f"#define _AL_HIDDEN_\n#define _GU_HIDDEN_\n{content}", encoding='utf-8')

    # 3. Neutralize the usual suspects
    toxic_headers = ["2.0L/PR/ultratypes.h", "2.0L/PR/abi.h", "2.0L/PR/mbi.h", "2.0L/PR/gbi.h", "2.0L/PR/os_libc.h"]
    for h_name in toxic_headers:
        h_path = decomp_root / "include" / h_name
        if h_path.exists():
            h_path.write_text("#include <n64_types.h>\n", encoding='utf-8')

def main():
    repo_root = Path("./")
    decomp_root = repo_root / "decomp-files"
    print("[>] SourceHarmonizer v83.2: Applying Snatch Guards")
    setup_headers(decomp_root)
    # ... rest of the file processing logic as before ...
