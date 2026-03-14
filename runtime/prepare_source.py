import os
import re
from pathlib import Path

# THE ATOMIC BRIDGE: Precise types and safe include order
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

// Match legacy SDK signed-ness exactly
typedef s32 OSId;
typedef s32 OSPri;
typedef u64 OSTime;
typedef void* OSMesg;
typedef struct { void* mt; void* full; int32_t count; } OSMesgQueue;

typedef struct { uint32_t status; uint32_t pc; uint64_t regs[32]; } OSContext;
typedef struct OSThread_s {
    struct OSThread_s *next;
    int32_t           priority;
    OSContext         context;
    uint8_t           stack_padding[128];
} OSThread;

/** 2. SYSTEM INCLUDES - Load these BEFORE any blockades **/
#ifdef __cplusplus
  #include <cstring>
  #include <cstdlib>
  #include <cstdio>
  #include <ctime>
  #include <cmath>
  extern "C" {
#else
  #include <string.h>
  #include <stdlib.h>
  #include <stdio.h>
  #include <time.h>
  #include <math.h>
#endif
#include <sched.h>
#include <unistd.h>

/** 3. PROJECT MACROS **/
#define PAIR(type, name) type name[2]
#define TUPLE(type, name) type name[3]
#define TUPLE_PAIR(type, name) type name[2][3]
#define FREE_LIST(type) struct { struct type *head; int32_t count; }

// Redirect bcopy to memmove to avoid the Android macro explosion
#define bcopy(src, dst, n) memmove(dst, src, n)

/** 4. N64 SDK BLOCKADE **/
#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _GBI_H_
#define _OS_H_
#define _OS_THREAD_H_
#define _OS_MESSAGE_H_
#define _OS_LIBC_H_
#define _SPTASK_H_
#define _LIBAUDIO_H_

typedef void* ALHeap;
typedef void* OSTask;
typedef struct ALGlobals_s { uint8_t d[1024]; } ALGlobals;

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#ifdef __cplusplus
}
#endif
#endif 
"""

def perform_surgical_neutralization():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    pr_dir = include_dir / "2.0L" / "PR"
    
    print("--- [v190.0] SURGICAL NEUTRALIZATION ---")
    
    # 1. Update the Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. Physically neutralize legacy PR headers
    # Instead of just blocking them, we empty them so they can't cause redefinitions.
    legacy_headers = [
        "os_thread.h", "os_message.h", "os_libc.h", 
        "gbi.h", "sptask.h", "libaudio.h", "ultra64.h"
    ]
    
    for h in legacy_headers:
        p = pr_dir / h
        if not p.exists(): p = include_dir / "2.0L" / h # Try parent if missing in PR
        
        if p.exists():
            print(f"Neutralizing legacy SDK: {p.name}")
            p.write_text("#include \"n64_types.h\"\n")

    # 3. Patch exceptasm.cpp redefinition
    asm_cpp = root / "Android/app/src/main/cpp/ultra/exceptasm.cpp"
    if asm_cpp.exists():
        text = asm_cpp.read_text()
        text = re.sub(r'typedef struct OSThread_s\s*\{.*?\}\s*OSThread\s*;', '/* Use Bridge */', text, flags=re.DOTALL)
        asm_cpp.write_text(text)

if __name__ == "__main__":
    perform_surgical_neutralization()
