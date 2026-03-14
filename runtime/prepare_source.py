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

// 1. Primitive N64 Types (64-bit safe)
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

// 2. Missing Graphics Types
typedef struct { uint8_t d[64]; } LookAt;
typedef struct { uint8_t d[64]; } Hilite;
typedef struct { uint8_t d[32]; } Light;
typedef struct { uint8_t d[32]; } PositionalLight;
typedef struct { uint8_t d[128]; } uSprite;

// 3. Hardware Structs (64-bit safe overrides)
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { uint8_t d[16]; } Vtx;
typedef struct { float d[16]; } BoneTransform;
typedef struct { BoneTransform *transforms; int count; } BoneTransformList;
typedef void* VLA; typedef void* FLA;
typedef struct { u32 t[16]; } OSTask_t;
typedef void (*OSErrorHandler)(void);
typedef struct { u32 d[16]; } OSLog;
typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;

typedef struct { void* handle; u32 type; u32 base; } OSPiHandle;
typedef struct { u32 hdr; void* buf; u32 len; OSMesgQueue* ret; } OSIoMesg;

typedef struct OSThread_s {
    struct OSThread_s *next; u32 priority;
    struct { u32 status; u32 pc; u32 sp; u32 d[16]; } context;
    uint8_t d[256]; 
} OSThread;

typedef struct { uint8_t d[64];  } OSContPad;
typedef struct { unsigned int w0, w1; } Acmd_words;
typedef union { Acmd_words words; long long force_align; } Acmd;
typedef s32 (*ALDMAproc)(s32 addr, s32 len, void *state);
typedef ALDMAproc (*ALDMANew)(void *state);

typedef u32 OSIntMask;

// 4. BLOCKADE - Prevent legacy headers from clashing
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

// 5. Memory Translation
#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

#if defined(__cplusplus)
extern "C" {
#endif
    static inline int sched_yield_compat(void) { return sched_yield(); }
#if defined(__cplusplus)
}
#endif

#endif // _N64_TYPES_H_
"""

def deploy_dynamic_patch():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    pr_folder = include_dir / "2.0L" / "PR"
    
    print("--- [v173.1] DEPLOYING FIXED UNIVERSAL INJECTION ---")
    
    # 1. Write the Master Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. Force ultra64.h to use our bridge (using triple quotes to avoid escape hell)
    ultra_h = include_dir / "2.0L" / "ultra64.h"
    if ultra_h.exists():
        content = """#ifndef _ULTRA64_H_
#define _ULTRA64_H_
#include "n64_types.h"
#endif
"""
        ultra_h.write_text(content)

    # 3. GUT problematic headers
    gut_list = [
        "ultratypes.h", "rcp.h", "R4300.h", "os.h", "os_thread.h", 
        "os_message.h", "os_libc.h", "os_pi.h", "os_convert.h", "os_cont.h", "region.h"
    ]
    
    for h in gut_list:
        p = pr_folder / h
        if p.exists():
            p.write_text("/* Handled by n64_types.h Injection */\n")

    # 4. Global project sweep
    for path in root.rglob("*.[ch]*"):
        if path.name == "n64_types.h" or "venv" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Use safer replacement to avoid breaking existing includes
            content = content.replace('#include "bool.h"', '#include "n64_types.h"')
            content = content.replace("sched_yield()", "sched_yield_compat()")

            if content != original:
                path.write_text(content)
        except Exception: continue

    print("--- Injection complete. Try running Ninja now! ---")

if __name__ == "__main__":
    deploy_dynamic_patch()
