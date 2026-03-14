import os
import re
from pathlib import Path

BASE_BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <time.h>
#include <sched.h>

// 1. Primitive N64 Types (64-bit safe mapping)
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;

typedef u32 OSId;
typedef u32 OSPri;
typedef u64 OSTime;
typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int32_t POLEF_STATE[4];
typedef int32_t ENVMIX_STATE[4];

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

// 2. Hardware/Graphics Structs
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { int16_t ob[3]; uint16_t flag; int16_t tc[2]; uint8_t cn[4]; } Vtx_t;
typedef union { Vtx_t v; long long force_align; } Vtx;
typedef struct { uint8_t d[64]; } LookAt;
typedef struct { uint8_t d[64]; } Hilite;
typedef struct { uint8_t d[32]; } Light;
typedef struct { uint8_t d[32]; } PositionalLight;
typedef struct { uint8_t d[128]; } uSprite;

// 3. Threading & OS Overrides
typedef struct OSThread_s {
    struct OSThread_s *next; u32 priority;
    uint8_t d[1024]; 
} OSThread;

typedef struct { u32 t[16]; } OSTask_t;
typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;
typedef struct { void* handle; u32 type; u32 base; } OSPiHandle;
typedef struct { u32 hdr; void* buf; u32 len; OSMesgQueue* ret; } OSIoMesg;
typedef struct { uint8_t d[64]; } OSContPad;

// 4. BLOCKADE - Total silencing of legacy SDK headers
#define _ULTRATYPES_H_
#define __OS_H__
#define _OS_THREAD_H_
#define _OS_MESSAGE_H_
#define _OS_CONT_H_
#define _OS_LIBC_H_
#define _GBI_H_
#define _ABI_H_
#define _SPTASK_H_
#define _ULTRALOG_H_
#define _ULTRAERROR_H_
#define _OS_CONVERT_H_
#define _OS_PI_H_
#define _RCP_H_
#define _R4300_H_
#define _REGION_H_
#define _ULTRA64_H_
#define _SCHED_H_

#if defined(__cplusplus)
extern "C" {
#endif
    static inline int sched_yield_compat(void) { return sched_yield(); }
#if defined(__cplusplus)
}
#endif

#endif // _N64_TYPES_H_
"""

def deploy_fortress_bridge():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    pr_folder = include_dir / "2.0L" / "PR"
    
    print("--- [v175.0] DEPLOYING FORTRESS BRIDGE ---")
    
    # 1. Ensure bridge exists
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. THE TOTAL GUT - Silence every file in the PR directory
    if pr_folder.exists():
        for header in pr_folder.glob("*.h"):
            header.write_text(f"/* Silenced by Fortress Bridge v175.0 */\n#include \"n64_types.h\"\n")

    # 3. Patch foundational headers
    for target in ["structs.h", "model.h", "2.0L/ultra64.h", "bool.h"]:
        p = include_dir / target
        if p.exists():
            original = p.read_text(errors='ignore')
            if 'include "n64_types.h"' not in original:
                p.write_text('#include "n64_types.h"\n' + original)

    # 4. Global source correction
    for path in root.rglob("*.[ch]*"):
        if "venv" in str(path) or path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            new_content = content.replace("sched_yield()", "sched_yield_compat()")
            if content != new_content:
                path.write_text(new_content)
        except: continue

if __name__ == "__main__":
    deploy_fortress_bridge()
