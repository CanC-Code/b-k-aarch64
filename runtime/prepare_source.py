import os
import re
from pathlib import Path

# THE ATOMIC BRIDGE v200.0: The absolute source of truth
# This version specifically fixes the cmath/math.h global namespace collapse.
BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

/** 1. BOOTSTRAP SYSTEM HEADERS **/
// We must load these before ANY N64 types to ensure the global namespace 
// is populated with the real AArch64 math/string/time functions.
#ifdef __cplusplus
  #include <iosfwd>
  #include <cmath>
  #include <cstring>
  #include <cstdlib>
  #include <cstdio>
  #include <ctime>
  #include <sched.h>
  extern "C" {
#else
  #include <math.h>
  #include <string.h>
  #include <stdlib.h>
  #include <stdio.h>
  #include <time.h>
  #include <sched.h>
#endif

#include <stdint.h>
#include <stddef.h>

/** 2. N64 PRIMITIVES **/
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;

/** 3. ADAPTIVE INTENT TYPES (Satisfying gu.h, libaudio, etc.) **/
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
typedef uint64_t Gfx;

/** 4. OS STRUCTURES **/
typedef void* OSMesg;
typedef struct { void* mt; void* full; int32_t count; } OSMesgQueue;
typedef struct OSThread_s {
    struct OSThread_s *next;
    int32_t           priority;
    uint8_t           dummy_context[512];
} OSThread;

/** 5. ANDROID COMPATIBILITY SHIMS **/
#undef bcopy
#define bcopy(src, dst, n) memmove(dst, src, n)
static inline int n64_yield(void) { return sched_yield(); }

/** 6. THE BLOCKADE - Prevent legacy headers from loading after this **/
#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _GBI_H_
#define _OS_H_
#define _GU_H_
#define _LIBAUDIO_H_
#define _SPTASK_H_
#define _BOOL_H_
#define _TIME_H_
#define _MATH_H_
#define _SCHED_H_

#ifdef __cplusplus
}
#endif

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#endif // _N64_TYPES_H_
"""

def automate_porting_logic():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    pr_dir = include_dir / "2.0L" / "PR"
    
    print("--- DEPLOYING ADAPTIVE PORTING TOOL v200.0 ---")
    
    # 1. Update the Bridge
    (include_dir / "n64_types.h").write_text(BRIDGE_CONTENT)

    # 2. NEUTRALIZE Shadowing (The Math/Cmath Fix)
    # We must rename math.h so the NDK finds its own math.h first.
    shadows = ["string.h", "bool.h", "time.h", "sched.h", "math.h", "malloc.h"]
    for s in shadows:
        p = include_dir / s
        if p.exists():
            print(f"Renaming clashing header: {s}")
            p.rename(p.with_suffix(".h.bak"))

    # 3. SURGICAL NEUTRALIZATION of PR headers
    # These are the files causing 'typedef redefinition'
    legacy = ["sptask.h", "libaudio.h", "gu.h", "gbi.h", "ultra64.h", "os.h", "mbi.h"]
    for h in legacy:
        p = pr_dir / h
        if not p.exists(): p = include_dir / "2.0L" / h
        if p.exists():
            p.write_text("#include \"n64_types.h\"\n")

    # 4. GLOBAL SOURCE REPAIR
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
            content = re.sub(r'typedef struct\s*\{.*?\}\s*(MtxF|Mtx|Vtx_t|LookAt|Hilite)\s*;', '/* Ref Bridge */', content, flags=re.DOTALL)

            if content != original:
                path.write_text(content)
        except: continue

if __name__ == "__main__":
    automate_porting_logic()
