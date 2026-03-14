import os
import re
from pathlib import Path

# THE ATOMIC BRIDGE: Modern AArch64 definitions for N64 types
BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>

/** 1. N64 PRIMITIVES - Satisfaction for core engine **/
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;

typedef int32_t OSPri;
typedef int32_t OSId;
typedef void* OSTask;
typedef void* ALHeap;
typedef void* OSMesg;
typedef struct { void* mt; void* full; int32_t count; } OSMesgQueue;

typedef struct OSThread_s {
    struct OSThread_s *next;
    int32_t           priority;
    uint8_t           context_dummy[512];
} OSThread;

typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { int16_t ob[3]; uint16_t flag; int16_t tc[2]; uint8_t cn[4]; } Vtx_t;
typedef union { Vtx_t v; long long force_align; } Vtx;

/** 2. ANDROID SYSTEM SHIELD **/
#ifdef __cplusplus
  #include <cstring>
  #include <cstdlib>
  #include <cstdio>
  #include <ctime>
  #include <sched.h>
  extern "C" {
#else
  #include <string.h>
  #include <stdlib.h>
  #include <stdio.h>
  #include <time.h>
  #include <sched.h>
#endif
    // Resolve the sched_yield conflict once and for all
    static inline int n64_yield(void) { return sched_yield(); }

#define _OS_H_
#define _ULTRA64_H_
#define _GBI_H_
#define _SCHED_H_
#define _BOOL_H_

#ifdef __cplusplus
  }
#endif

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#endif
"""

def transform_project():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- STARTING SURGICAL TRANSFORMATION ---")
    
    # 1. Update the bridge
    (include_dir / "n64_types.h").write_text(BRIDGE_CONTENT)

    # 2. NEUTRALIZE the legacy SDK (PR folder)
    # We replace their content with our bridge so they stop causing redefinition errors.
    pr_dir = include_dir / "2.0L" / "PR"
    neutralize = ["sched.h", "os_thread.h", "os_message.h", "gbi.h", "os.h", "ultra64.h"]
    for h in neutralize:
        p = pr_dir / h
        if p.exists():
            print(f"Neutralizing legacy header: {h}")
            p.write_text("#include \"n64_types.h\"\n")

    # 3. TRANSFORM Source Files
    # We need to swap any direct calls to hardware-clashing functions
    for path in root.rglob("*.[ch]*"):
        if "n64_types.h" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Fix pathing errors for decompression tools
            content = content.replace('tools/rare_decompression.h', 'rare_decompression.h')
            
            # Redirect sched_yield to our safe inline
            content = content.replace('sched_yield()', 'n64_yield()')
            
            if content != original:
                path.write_text(content)
        except: continue

if __name__ == "__main__":
    transform_project()
