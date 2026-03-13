import os
import re
from pathlib import Path

BASE_BRIDGE_CONTENT = """
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// 1. Primitive Types
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

// 2. Hardware Structs (64-bit safe overrides)
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

// 3. System Standard Libraries
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>

// 4. PREEMPTIVE BLOCKADE - Prevent N64 headers from redefining types
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
#define _REGION_H_
#define _GU_H_

// 5. Memory Mapper
#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

#endif // _N64_TYPES_H_
"""

def deploy_dynamic_patch():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v168.0] DEPLOYING TOTAL BLOCKADE ---")
    
    # 1. Write the Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. Correct the Rare Decompression Include Paths in C++ files
    android_cpp_dir = root / "Android" / "app" / "src" / "main" / "cpp"
    for path in android_cpp_dir.rglob("*.cpp"):
        try:
            content = path.read_text(errors='ignore')
            if '#include "tools/rare_decompression.h"' in content:
                content = content.replace('#include "tools/rare_decompression.h"', '#include "rare_decompression.h"')
                path.write_text(content)
        except Exception: pass

    # 3. Clean up legacy headers in decomp-files
    for sh in ["string.h", "math.h", "stdio.h", "stdlib.h", "bool.h", "basic_types.h"]:
        p = include_dir / sh
        if p.exists(): p.unlink()

    print("--- Blockade Deployed. Run Ninja! ---")

if __name__ == "__main__":
    deploy_dynamic_patch()
