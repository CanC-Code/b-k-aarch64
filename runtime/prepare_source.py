import os
import re
from pathlib import Path

# THE ATOMIC BRIDGE: Modern AArch64 definitions for N64 hardware structures
BRIDGE_CONTENT = r"""
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

/** 2. HARDWARE TYPES (Satisfying gu.h and libaudio.h) **/
typedef void* OSTask;
typedef void* ALHeap;
typedef struct { float m[4][4]; } MtxF;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t col[3]; int8_t dir[3]; } Light_t;
typedef union { Light_t l; long long force_align; } Light;
typedef struct { uint8_t col[3]; uint8_t pad; } Ambient_t;
typedef union { Ambient_t a; long long force_align; } Ambient;
typedef struct { int16_t x, y, z; } LookAt_t;
typedef union { LookAt_t l; long long force_align; } LookAt;
typedef struct { int16_t x, y, z; } Hilite_t;
typedef union { Hilite_t h; long long force_align; } Hilite;
typedef void* uSprite;

/** 3. SYSTEM INCLUDES - Must load BEFORE blockades **/
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

// Redirect bcopy to memmove to avoid the Android macro explosion
#undef bcopy
#define bcopy(src, dst, n) memmove(dst, src, n)

/** 4. THE BLOCKADE **/
#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _GBI_H_
#define _OS_H_
#define _GU_H_
#define _LIBAUDIO_H_
#define _SPTASK_H_
#define _BOOL_H_

#ifdef __cplusplus
}
#endif

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#endif // _N64_TYPES_H_
"""

def perform_transformation():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    pr_dir = include_dir / "2.0L" / "PR"
    
    print("--- DEPLOYING ADAPTIVE TRANSFORMATION ---")
    
    # 1. Update the bridge with satisfied Hardware types
    (include_dir / "n64_types.h").write_text(BRIDGE_CONTENT)

    # 2. NEUTRALIZE conflicting project headers (Shadowing fix)
    # Renaming them forces the NDK to find the system versions of string.h and bool.h
    shadows = ["string.h", "bool.h", "time.h", "sched.h"]
    for s in shadows:
        p = include_dir / s
        if p.exists():
            print(f"Neutralizing project shadowing: {s}")
            p.rename(p.with_suffix(".h.bak"))

    # 3. SURGICAL PURGE: Physically empty legacy SDK headers
    # This ensures the compiler ONLY uses our n64_types.h
    legacy_headers = [
        "sptask.h", "libaudio.h", "gu.h", "gbi.h", "ultra64.h", 
        "os_thread.h", "os_message.h", "os_libc.h"
    ]
    for h in legacy_headers:
        p = pr_dir / h
        if not p.exists(): p = include_dir / "2.0L" / h
        if p.exists():
            p.write_text("#include \"n64_types.h\"\n")

    # 4. PATH REPAIR: Normalize include paths in source files
    for path in root.rglob("*.[ch]*"):
        try:
            content = path.read_text(errors='ignore')
            # Fix the "tools/rare_decompression.h" missing error
            new_content = content.replace('#include "tools/rare_decompression.h"', '#include "rare_decompression.h"')
            
            # Remove any local redefinitions of MtxF/Mtx in structs.h
            if "structs.h" in str(path):
                new_content = re.sub(r'typedef struct\s*\{.*?\}\s*(MtxF|Mtx)\s*;', '/* Ref Bridge */', new_content, flags=re.DOTALL)
            
            if content != new_content:
                path.write_text(new_content)
        except: continue

if __name__ == "__main__":
    perform_transformation()
