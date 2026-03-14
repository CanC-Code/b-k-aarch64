import os
from pathlib import Path

BASE_BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

/** 1. ATOMIC TYPES - MUST BE FIRST **/
#include <stdint.h>
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

/** 2. SYSTEM INCLUDES **/
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <time.h>
#include <sched.h>

/** 3. HARDWARE STRUCTS **/
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { int16_t ob[3]; uint16_t flag; int16_t tc[2]; uint8_t cn[4]; } Vtx_t;
typedef union { Vtx_t v; long long force_align; } Vtx;
typedef struct { uint8_t d[64]; } LookAt;
typedef struct { uint8_t d[64]; } Hilite;
typedef struct { uint8_t d[32]; } Light;
typedef struct { uint8_t d[32]; } PositionalLight;

/** 4. OS/THREADING SHIMS **/
typedef struct OSThread_s {
    struct OSThread_s *next; uint32_t priority;
    uint8_t d[1024]; 
} OSThread;
typedef uint32_t OSId;
typedef uint32_t OSPri;
typedef uint64_t OSTime;
typedef struct { uint32_t t[16]; } OSTask_t;
typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;

/** 5. BLOCKADE MASKS **/
#define _ULTRATYPES_H_
#define __OS_H__
#define _OS_THREAD_H_
#define _OS_MESSAGE_H_
#define _GBI_H_
#define _ULTRA64_H_
#define _REGION_H_

#if defined(__cplusplus)
extern "C" {
#endif
    static inline int sched_yield_compat(void) { return sched_yield(); }
#if defined(__cplusplus)
}
#endif

#endif // _N64_TYPES_H_
"""

def deploy_atomic_bridge():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v175.1] DEPLOYING ATOMIC FOUNDATION ---")
    
    # 1. Write the Atomic Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. SEVER the circular dependency
    # We remove the bridge inclusion FROM foundational headers to prevent recursion
    # Instead, we force the compiler to load the bridge via the command line or Mother Header
    foundational = ["string.h", "structs.h", "model.h"]
    for f in foundational:
        p = include_dir / f
        if p.exists():
            content = p.read_text(errors='ignore')
            # Remove existing bridge includes to let the "Forced Include" handle it
            content = content.replace('#include "n64_types.h"', '/* Bridge injected globally */')
            p.write_text(content)

    # 3. The "Mother Header" remains the gateway
    ultra_h = include_dir / "2.0L" / "ultra64.h"
    if ultra_h.exists():
        ultra_h.write_text("#ifndef _ULTRA64_H_\n#define _ULTRA64_H_\n#include \"n64_types.h\"\n#endif\n")

    # 4. Global symbol swap
    for path in root.rglob("*.[ch]*"):
        if "venv" in str(path) or path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            new_content = content.replace("sched_yield()", "sched_yield_compat()")
            if content != new_content:
                path.write_text(new_content)
        except: continue

if __name__ == "__main__":
    deploy_atomic_bridge()
