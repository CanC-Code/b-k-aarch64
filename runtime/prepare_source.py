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

typedef int32_t OSId;
typedef int32_t OSPri;
typedef uint64_t OSTime;
typedef void* OSMesg;
typedef struct { void* mt; void* full; int32_t count; } OSMesgQueue;

typedef struct { uint32_t status; uint32_t pc; uint64_t regs[32]; } OSContext;
typedef struct OSThread_s {
    struct OSThread_s *next;
    int32_t           priority;
    OSContext         context;
    uint8_t           stack_padding[128];
} OSThread;

/** 2. SYSTEM INCLUDES - Forced first **/
#ifdef __cplusplus
  #include <cstring>
  #include <cstdlib>
  #include <cstdio>
  #include <ctime>
  #include <sched.h> // The real system scheduler
  extern "C" {
#else
  #include <string.h>
  #include <stdlib.h>
  #include <stdio.h>
  #include <time.h>
  #include <sched.h>
#endif

// Prevent legacy headers from ever loading
#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _GBI_H_
#define _OS_H_
#define _OS_THREAD_H_
#define _OS_MESSAGE_H_
#define _OS_LIBC_H_
#define _BOOL_H_

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

def deploy_atomic_isolation():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v194.0] DEPLOYING ATOMIC ISOLATION ---")
    
    # 1. Rename clashing project headers to prevent shadowing system libraries
    clashes = ["string.h", "bool.h", "time.h", "sched.h"]
    for c in clashes:
        p = include_dir / c
        if p.exists():
            new_p = include_dir / f"n64_project_{c}"
            print(f"Renaming {c} -> {new_p.name}")
            p.rename(new_p)

    # 2. Deploy the isolated bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 3. GLOBAL PATH REPAIR: Fix "tools/header.h" to "header.h"
    # This solves the "rare_decompression.h not found" error
    for path in root.rglob("*.[ch]*"):
        if "n64_types.h" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            new_content = content.replace('#include "tools/rare_decompression.h"', '#include "rare_decompression.h"')
            if content != new_content:
                path.write_text(new_content)
        except: continue

if __name__ == "__main__":
    deploy_atomic_isolation()
