import os
import re
from pathlib import Path

# THE ATOMIC BRIDGE: No dependencies, real anatomical members, and macro support.
BASE_BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>

/** 1. N64 PRIMITIVES - DEFINED FIRST **/
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

/** 2. PROJECT MACROS & DUMMIES **/
#define PAIR(type, name) type name[2]
#define TUPLE(type, name) type name[3]
#define TUPLE_PAIR(type, name) type name[2][3]
#define FREE_LIST(type) struct { struct type *head; int32_t count; }

// Dummy structs to satisfy macro expansions in structs.h
struct struct12s;
struct struct_68_s;
struct BKModelBin;
struct BKVertexList;

/** 3. C++ NAMESPACE SAFETY **/
#ifdef __cplusplus
  #include <cstring>
  #include <cstdlib>
  #include <cstdio>
  using namespace std;
  extern "C" {
#else
  #include <string.h>
  #include <stdlib.h>
  #include <stdio.h>
#endif

typedef void* OSMesg;
typedef struct { void* mt; void* full; int32_t count; } OSMesgQueue;
typedef struct OSThread_s { struct OSThread_s *next; int32_t priority; uint8_t d[256]; } OSThread;
typedef uint32_t OSId;
typedef uint32_t OSPri;
typedef uint64_t OSTime;
typedef void* ALHeap;
typedef void* OSTask;

#ifdef __cplusplus
}
#endif

#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _GBI_H_
#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#endif // _N64_TYPES_H_
"""

def deploy_total_isolation():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v183.0] DEPLOYING TOTAL ISOLATION PATCH ---")
    
    # 1. Update the Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. NEUTRALIZE string.h and bool.h
    # These often shadow system headers in NDK builds
    for h in ["string.h", "bool.h"]:
        p = include_dir / h
        if p.exists():
            p.write_text("#include \"n64_types.h\"\n")

    # 3. SURGERY on structs.h and model.h
    # We strip their internal includes to break the circular dependency loop
    for target in ["structs.h", "model.h"]:
        p = include_dir / target
        if p.exists():
            text = p.read_text(errors='ignore')
            # Remove existing Mtx/Vtx definitions that clash with our new bridge
            text = re.sub(r'typedef struct\s*\{.*?\}\s*(MtxF|Mtx|Vtx_t)\s*;', '/* Defined in Bridge */', text, flags=re.DOTALL)
            text = re.sub(r'typedef union\s*\{.*?\}\s*Vtx\s*;', '/* Defined in Bridge */', text, flags=re.DOTALL)
            # Prepend bridge
            if '#include "n64_types.h"' not in text:
                text = '#include "n64_types.h"\n' + text
            p.write_text(text)

    # 4. FIX path for rare_decompression
    rare_cpp = root / "Android/app/src/main/cpp/tools/rare_decompression.cpp"
    if rare_cpp.exists():
        text = rare_cpp.read_text()
        text = text.replace('#include "tools/rare_decompression.h"', '#include "rare_decompression.h"')
        rare_cpp.write_text(text)

if __name__ == "__main__":
    deploy_total_isolation()
