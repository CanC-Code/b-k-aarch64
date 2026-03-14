import os
from pathlib import Path

BASE_BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

/** 1. ATOMIC FOUNDATION - DEFINED BEFORE ANY INCLUDES **/
#include <stdint.h>

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

/** 3. OS & HARDWARE SHIMS **/
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
typedef struct { void* handle; u32 type; u32 base; } OSPiHandle;
typedef struct { u32 hdr; void* buf; u32 len; OSMesgQueue* ret; } OSIoMesg;
typedef struct { uint8_t d[64]; } OSContPad;
typedef void* ALHeap;
typedef void* OSTask;

/** 4. BLOCKADE MASKS **/
#define _ULTRATYPES_H_
#define __OS_H__
#define _OS_THREAD_H_
#define _OS_MESSAGE_H_
#define _OS_CONT_H_
#define _OS_LIBC_H_
#define _GBI_H_
#define _ABI_H_
#define _SPTASK_H_
#define _REGION_H_
#define _ULTRA64_H_
#define _SCHED_H_
#define _BOOL_H_

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
    pr_folder = include_dir / "2.0L" / "PR"
    
    print("--- [v176.0] DEPLOYING ATOMIC FOUNDATION ---")
    
    # 1. Write the Atomic Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. SEVER the circular dependency
    # Remove bridge inclusion from foundational headers; we use a command-line forced include instead.
    for f in ["string.h", "structs.h", "model.h", "bool.h"]:
        p = include_dir / f
        if p.exists():
            content = p.read_text(errors='ignore')
            # Prevent bool redeclaration
            if f == "bool.h":
                p.write_text("#include <stdbool.h>\n")
                continue
            content = content.replace('#include "n64_types.h"', '/* Bridge provided by build system */')
            p.write_text(content)

    # 3. GUT the legacy PR folder headers
    if pr_folder.exists():
        for header in pr_folder.glob("*.h"):
            header.write_text(f"/* Silenced. Use n64_types.h */\n")

    # 4. Patch Mother Header
    ultra_h = include_dir / "2.0L" / "ultra64.h"
    if ultra_h.exists():
        ultra_h.write_text("#include \"n64_types.h\"\n")

    # 5. Global symbol swap
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
