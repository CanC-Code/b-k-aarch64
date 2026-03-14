import os
import re
from pathlib import Path

# THE ATOMIC BRIDGE: Fixed include order and safe blockades
BASE_BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>

/** 1. N64 PRIMITIVES - MUST BE AT THE VERY TOP **/
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

typedef uint32_t OSId;
typedef uint32_t OSPri;
typedef uint64_t OSTime;
typedef void* OSMesg;
typedef struct { void* mt; void* full; int32_t count; } OSMesgQueue;
typedef void* OSTask;
typedef void* ALHeap;

typedef struct { uint32_t status; uint32_t pc; uint64_t regs[32]; } OSContext;
typedef struct OSThread_s {
    struct OSThread_s *next;
    int32_t           priority;
    OSContext         context;
    uint8_t           stack_padding[128];
} OSThread;

/** 2. SYSTEM INCLUDES - Load these BEFORE blocking anything **/
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

/** 3. N64 SDK BLOCKADE - Use ONLY guards unique to the N64 headers **/
#define __OS_H__
#define _OS_H_
#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _GBI_H_
#define _OS_THREAD_H_
#define _OS_MESSAGE_H_
#define _OS_CONT_H_
#define _OS_LIBC_H_
#define _LIBAUDIO_H_
#define _SCHED_H_  /* N64's sched.h, hopefully doesn't clash with system <sched.h> */

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#ifdef __cplusplus
}
#endif

#endif // _N64_TYPES_H_
"""

def deploy_atomic_foundation():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v189.0] DEPLOYING ATOMIC FOUNDATION ---")
    
    # 1. Rename only the most problematic project headers
    # We'll leave time.h alone for a moment to see if order-fixing works
    clashes = ["string.h", "bool.h", "sched.h"]
    for c in clashes:
        p = include_dir / c
        if p.exists():
            new_p = include_dir / f"n64_project_{c}"
            p.rename(new_p)

    # 2. Deploy updated bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 3. Clean up exceptasm.cpp (Remove local redefinitions)
    asm_cpp = root / "Android/app/src/main/cpp/ultra/exceptasm.cpp"
    if asm_cpp.exists():
        text = asm_cpp.read_text()
        text = re.sub(r'typedef struct OSThread_s\s*\{.*?\}\s*OSThread\s*;', '/* Bridge-Defined */', text, flags=re.DOTALL)
        text = text.replace('NULL', 'nullptr')
        asm_cpp.write_text(text)

    # 4. Fix rare_decompression pathing globally
    for path in root.rglob("*.[ch]*"):
        try:
            content = path.read_text(errors='ignore')
            if 'tools/rare_decompression.h' in content:
                path.write_text(content.replace('tools/rare_decompression.h', 'rare_decompression.h'))
        except: continue

if __name__ == "__main__":
    deploy_atomic_foundation()
