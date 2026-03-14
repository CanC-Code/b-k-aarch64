import os
import re
from pathlib import Path

# THE ATOMIC BRIDGE: Unified AArch64 definitions for N64 hardware
BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

/** 1. BOOTSTRAP SYSTEM HEADERS **/
// Load these FIRST to populate the global namespace before we define N64 types.
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

#include <stdint.h>

/** 2. N64 PRIMITIVES **/
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;

/** 3. HARDWARE TYPES (Satisfying gu.h, libaudio, and sptask) **/
typedef void* OSTask;
typedef void* ALHeap;
typedef void* uSprite;
typedef uint64_t Gfx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { int32_t m[4][4]; } Mtx;

typedef struct { uint8_t col[3]; int8_t dir[3]; } Light_t;
typedef union { Light_t l; long long force_align; } Light;
typedef struct { int16_t x, y, z; } LookAt_t;
typedef union { LookAt_t l; long long force_align; } LookAt;
typedef struct { int16_t x, y, z; } Hilite_t;
typedef union { Hilite_t h; long long force_align; } Hilite;

/** 4. OS STRUCTURES **/
typedef void* OSMesg;
typedef struct { void* mt; void* full; int32_t count; } OSMesgQueue;
typedef int32_t OSPri;
typedef struct OSThread_s {
    struct OSThread_s *next;
    int32_t           priority;
    uint8_t           context_dummy[512];
} OSThread;

/** 5. ANDROID SHIMS **/
#undef bcopy
#define bcopy(src, dst, n) memmove(dst, src, n)
static inline int n64_yield(void) { return sched_yield(); }

/** 6. THE BLOCKADE **/
#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _GBI_H_
#define _OS_H_
#define _GU_H_
#define _LIBAUDIO_H_
#define _SPTASK_H_
#define _BOOL_H_

typedef struct ALGlobals_s { uint8_t d[1024]; } ALGlobals;

#ifdef __cplusplus
}
#endif

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#endif // _N64_TYPES_H_
"""

def transform_and_adapt():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    pr_dir = include_dir / "2.0L" / "PR"
    
    print("--- DEPLOYING SURGICAL TRANSFORMATION v201.0 ---")
    
    # 1. Update the bridge with missing types found in log
    (include_dir / "n64_types.h").write_text(BRIDGE_CONTENT)

    # 2. NEUTRALIZE shadow clashing headers
    # Renaming forces the NDK to use system headers for string/math/time.
    shadows = ["string.h", "bool.h", "time.h", "sched.h", "math.h"]
    for s in shadows:
        p = include_dir / s
        if p.exists():
            print(f"Neutralizing project shadow: {s}")
            p.rename(p.with_suffix(".h.bak"))

    # 3. SURGICAL NEUTRALIZATION of legacy SDK
    # We replace their content with our bridge to stop redefinition loops.
    legacy_headers = ["sptask.h", "libaudio.h", "gu.h", "gbi.h", "ultra64.h", "os.h"]
    for h in legacy_headers:
        p = pr_dir / h
        if not p.exists(): p = include_dir / "2.0L" / h
        if p.exists():
            print(f"Adapting legacy header: {h}")
            p.write_text("#include \"n64_types.h\"\n")

    # 4. Global Source Surgery
    for path in root.rglob("*.[ch]*"):
        if "n64_types.h" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Fix pathing
            content = content.replace('#include "tools/rare_decompression.h"', '#include "rare_decompression.h"')
            
            # Fix sched_yield
            content = content.replace('sched_yield()', 'n64_yield()')
            
            # Remove local structure redefinitions (MtxF, Mtx, etc)
            content = re.sub(r'typedef struct\s*\{.*?\}\s*(MtxF|Mtx|Vtx_t)\s*;', '/* Ref Bridge */', content, flags=re.DOTALL)

            if content != original:
                path.write_text(content)
        except: continue

if __name__ == "__main__":
    transform_and_adapt()
