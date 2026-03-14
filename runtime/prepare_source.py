import os
import re
from pathlib import Path

# THE ATOMIC BRIDGE: The single source of truth for N64 types
BASE_BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>

/** 1. N64 PRIMITIVES **/
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;

typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { int16_t ob[3]; uint16_t flag; int16_t tc[2]; uint8_t cn[4]; } Vtx_t;
typedef union { Vtx_t v; long long force_align; } Vtx;

/** 2. SYSTEM HEADERS - Forced first to prevent shadowing **/
#ifdef __cplusplus
  #include <cstring>
  #include <cstdlib>
  #include <cstdio>
  #include <ctime>
  extern "C" {
#else
  #include <string.h>
  #include <stdlib.h>
  #include <stdio.h>
  #include <time.h>
#endif

typedef void* OSMesg;
typedef struct { void* mt; void* full; int32_t count; } OSMesgQueue;
typedef struct OSThread_s { struct OSThread_s *next; int32_t priority; uint8_t d[256]; } OSThread;
typedef uint32_t OSId;
typedef uint32_t OSPri;
typedef uint64_t OSTime;

/** 3. PROJECT BLOCKADE **/
#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _GBI_H_
#define _OS_H_
#define _BOOL_H_ 
#define _TIME_H_

typedef void* ALHeap;
typedef void* OSTask;

#ifdef __cplusplus
}
#endif

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#endif // _N64_TYPES_H_
"""

def deploy_neutralization():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v191.0] DEPLOYING SURGICAL NEUTRALIZATION ---")
    
    # 1. Neutralize Clashing Headers
    # We rename them so the compiler CANNOT find them as "string.h"
    clash_list = ["string.h", "bool.h", "time.h", "sched.h"]
    for header in clash_list:
        p = include_dir / header
        if p.exists():
            print(f"Neutralizing {header}...")
            # We rename to .bak so they are out of the include path
            p.rename(p.with_suffix('.h.bak'))

    # 2. Update the Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 3. Patch structs.h and model.h to stop redefinitions
    # These files often try to redefine Mtx/Vtx
    for target in ["structs.h", "model.h"]:
        p = include_dir / target
        if p.exists():
            content = p.read_text(errors='ignore')
            # Remove MtxF, Mtx, Vtx, and ALHeap redefinitions
            content = re.sub(r'typedef struct\s*\{.*?\}\s*(MtxF|Mtx|Vtx_t|ALHeap)\s*;', '/* Ref Bridge */', content, flags=re.DOTALL)
            content = re.sub(r'typedef union\s*\{.*?\}\s*Vtx\s*;', '/* Ref Bridge */', content, flags=re.DOTALL)
            # Ensure n64_types.h is included
            if '#include "n64_types.h"' not in content:
                content = '#include "n64_types.h"\n' + content
            p.write_text(content)

if __name__ == "__main__":
    deploy_neutralization()
