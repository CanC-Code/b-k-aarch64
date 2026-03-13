import os
import re
from pathlib import Path

BASE_BRIDGE_CONTENT = """
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

// 1. Primitive N64 Types
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;

// Missing SDK Base Types for orphaned headers
typedef u32 OSId;
typedef u32 OSPri;
typedef u64 OSTime;
typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];

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

// 64-bit safe Pi Handle and IO Message
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

// 3. PREEMPTIVE BLOCKADE - Prevent N64 headers from redefining types
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

// 4. Memory Mapper
#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

#endif // _N64_TYPES_H_
"""

def deploy_dynamic_patch():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    android_cpp_dir = root / "Android" / "app" / "src" / "main" / "cpp"
    
    print("--- [v169.0] DEPLOYING FULL SPECTRUM BRIDGE ---")
    
    # 1. Write the Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. Patch every file in the project
    clash_types = {"Gfx", "Acmd", "OSTask_t", "MtxF", "Mtx", "Vtx", "BoneTransform", "BoneTransformList", "VLA", "FLA", "OSLog", "OSRegion", "RamRomBuffer", "OSThread", "OSMesgQueue", "OSContPad", "OSThread_s", "OSPiHandle", "OSIoMesg"}

    for path in list(decomp.rglob("*.[ch]")) + list(android_cpp_dir.rglob("*.[ch]pp")):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Ensure bridge is first
            if '#include "n64_types.h"' not in content:
                content = '#include "n64_types.h"\\n' + content
                
            # Scrub Boolean redefinitions
            content = content.replace("typedef int bool;", "/* Scrubbed bool */")
            
            # Path fix for decompression header
            content = content.replace('#include "tools/rare_decompression.h"', '#include "rare_decompression.h"')

            # Advanced: Scrub redefinitions of structs we handle in bridge
            for ct in clash_types:
                content = re.sub(r'typedef\s+struct\s+' + ct + r'\s*\{[^}]*\}\s*' + ct + r'\s*;', f'/* Scrubbed {ct} */', content)
                content = re.sub(r'typedef\s+struct\s+' + ct + r'_s\s*\{[^}]*\}\s*' + ct + r'\s*;', f'/* Scrubbed {ct} */', content)

            if content != original:
                path.write_text(content)
        except Exception: continue

    # 3. Restore standard library headers if they were deleted by previous scripts
    # We need Android to handle time.h correctly
    for sh in ["string.h", "math.h", "stdio.h", "stdlib.h", "time.h"]:
        p = include_dir / sh
        if p.exists(): p.unlink() # Delete them so Android's headers are used

    print("--- Bridge Deployed. Run Ninja! ---")

if __name__ == "__main__":
    deploy_dynamic_patch()
