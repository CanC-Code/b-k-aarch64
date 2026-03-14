import os
import re
from pathlib import Path

# Updated Bridge with Macro Support and C++ safety
BASE_BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>

/** 1. C++ BOOL SAFETY **/
#ifdef __cplusplus
  #include <stdbool.h>
#else
  typedef uint8_t bool;
#endif
#define _BOOL_H_ // Block project bool.h

/** 2. N64 PRIMITIVES **/
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;

/** 3. PROJECT MACROS (The 'FREE_LIST' and 'PAIR' fixes) **/
#define PAIR(type, name) type name[2]
#define TUPLE(type, name) type name[3]
#define TUPLE_PAIR(type, name) type name[2][3]
#define FREE_LIST(type) struct { type *head; int32_t count; }

/** 4. ANATOMICAL MOCKS **/
typedef struct OSThread_s {
    struct OSThread_s *next;
    int32_t           priority;
    struct { uint32_t status; uint32_t pc; uint64_t regs[32]; } context;
} OSThread;

typedef void* OSMesg;
typedef struct { void* mt; void* full; int32_t count; } OSMesgQueue;
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;

/** 5. BLOCKADE **/
#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _LIBAUDIO_H_
#define _GBI_H_

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

typedef void* ALHeap;
typedef void* OSTask;

#endif // _N64_TYPES_H_
"""

def deploy_universal_glue():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v182.0] DEPLOYING UNIVERSAL GLUE ---")
    
    # 1. Update the Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. FIX: rare_decompression pathing
    # The build looks for tools/rare_decompression.h but it's likely just rare_decompression.h
    rare_cpp = root / "Android/app/src/main/cpp/tools/rare_decompression.cpp"
    if rare_cpp.exists():
        text = rare_cpp.read_text()
        text = text.replace('#include "tools/rare_decompression.h"', '#include "rare_decompression.h"')
        rare_cpp.write_text(text)

    # 3. SURGERY: Kill the project's bool.h
    bool_h = include_dir / "bool.h"
    if bool_h.exists():
        bool_h.write_text("// Nuked for C++ compatibility\n")

    # 4. Cleanup structs.h
    structs_h = include_dir / "structs.h"
    if structs_h.exists():
        text = structs_h.read_text(errors='ignore')
        # Ensure it doesn't redefine what we put in the bridge
        text = re.sub(r'typedef struct\s*\{.*?\}\s*(MtxF|Mtx)\s*;', '/* Ref in bridge */', text, flags=re.DOTALL)
        # Ensure it sees our bridge macros
        if '#include "n64_types.h"' not in text:
            text = '#include "n64_types.h"\n' + text
        structs_h.write_text(text)

if __name__ == "__main__":
    deploy_universal_glue()
