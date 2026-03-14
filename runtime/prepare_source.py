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

/** 1. MANDATORY MACRO BLOCKADE **/
// This poisons the guards so the compiler skips the legacy SDK headers entirely
#define _ULTRATYPES_H_
#define __OS_H__
#define _OS_H_
#define _OS_THREAD_H_
#define _OS_MESSAGE_H_
#define _OS_CONT_H_
#define _OS_LIBC_H_
#define _GBI_H_
#define _ABI_H_
#define _SPTASK_H_
#define _ULTRA64_H_
#define _REGION_H_
#define _SCHED_H_
#define _OS_PI_H_

/** 2. N64 PRIMITIVES (64-bit Safe) **/
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

/** 3. ENGINE STRUCTS **/
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { int16_t ob[3]; uint16_t flag; int16_t tc[2]; uint8_t cn[4]; } Vtx_t;
typedef union { Vtx_t v; long long force_align; } Vtx;

typedef uint32_t OSId;
typedef uint32_t OSPri;
typedef uint64_t OSTime;
typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;

typedef struct OSThread_s {
    struct OSThread_s *next;
    uint32_t priority;
    uint8_t d[1024]; 
} OSThread;

typedef void* ALHeap;
typedef void* OSTask;

#if defined(__cplusplus)
extern "C" {
#endif
    static inline int sched_yield_compat(void) { return sched_yield(); }
#if defined(__cplusplus)
}
#endif

#endif // _N64_TYPES_H_
"""

def deploy_absolute_suppression():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v178.1] DEPLOYING ABSOLUTE SUPPRESSION ---")
    
    # 1. Write the Shielded Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. SURGERY: Force structs.h to be compliant
    structs_h = include_dir / "structs.h"
    if structs_h.exists():
        text = structs_h.read_text(errors='ignore')
        # Wipe out clashing definitions that would error on redefinition
        text = re.sub(r'typedef struct\s*\{.*?\}\s*MtxF\s*;', '/* Ref in bridge */', text, flags=re.DOTALL)
        text = re.sub(r'typedef struct\s*\{.*?\}\s*Mtx\s*;', '/* Ref in bridge */', text, flags=re.DOTALL)
        text = text.replace('ALHeap', 'void*')
        # Stop the inclusion cascade
        text = text.replace('#include "2.0L/ultra64.h"', '/* Suppressed */')
        text = text.replace('#include "ultra64.h"', '/* Suppressed */')
        structs_h.write_text(text)

    # 3. Suppress the PR folder content physically
    pr_path = include_dir / "2.0L" / "PR"
    if pr_path.exists():
        for h_file in pr_path.glob("*.h"):
            h_file.write_text("#include \"n64_types.h\"\n")

    # 4. Final Sweep for NativeBridge.cpp
    bridge_cpp = root / "Android/app/src/main/cpp/ultra/NativeBridge.cpp"
    if bridge_cpp.exists():
        text = bridge_cpp.read_text()
        # Fix sched_yield calls specifically for Android compatibility
        if 'sched_yield()' in text:
            text = text.replace('sched_yield()', 'sched_yield_compat()')
        bridge_cpp.write_text(text)

if __name__ == "__main__":
    deploy_absolute_suppression()
