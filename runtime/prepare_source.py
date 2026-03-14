import os
import re
from pathlib import Path

# THE ATOMIC BRIDGE: Complete definitions.
BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

/** 1. BOOTSTRAP SYSTEM HEADERS **/
#ifdef __cplusplus
  #include <cstring>
  #include <cstdlib>
  #include <cstdio>
  #include <ctime>
  extern "C" {
      int sched_yield(void);
  }
#else
  #include <string.h>
  #include <stdlib.h>
  #include <stdio.h>
  #include <time.h>
  extern int sched_yield(void);
#endif

#include <stdint.h>

/** 2. N64 PRIMITIVES **/
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;

/** 3. HARDWARE TYPES **/
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
typedef int32_t OSId;
typedef struct { uint32_t status; uint32_t pc; uint64_t regs[32]; } OSContext;
typedef struct OSThread_s {
    struct OSThread_s *next;
    int32_t           priority;
    OSContext         context;
    uint8_t           stack_padding[128];
} OSThread;

/** 5. ANDROID COMPATIBILITY **/
#undef bcopy
#define bcopy(src, dst, n) memmove((dst), (src), (n))
static inline int n64_yield(void) { return sched_yield(); }

/** 6. MACRO BLOCKADE **/
#define _ULTRATYPES_H_

#ifdef __cplusplus
}
#endif

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#endif // _N64_TYPES_H_
"""

def perform_precision_strike():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    pr_dir = include_dir / "2.0L" / "PR"
    
    print("--- DEPLOYING PRECISION STRIKE ---")
    
    # 1. Update the bridge
    (include_dir / "n64_types.h").write_text(BRIDGE_CONTENT)

    # 2. NEUTRALIZE shadow clashing headers
    shadows = ["string.h", "bool.h", "time.h", "sched.h", "math.h", "malloc.h"]
    for s in shadows:
        p = include_dir / s
        if p.exists(): p.rename(p.with_suffix(".bak"))

    # 3. SURGICAL TRUNCATION OF LEGACY HEADERS
    
    # A. Fix os_libc.h (The bcopy macro collision)
    os_libc = pr_dir / "os_libc.h"
    if os_libc.exists():
        lines = os_libc.read_text(errors='ignore').split('\n')
        # Filter out the bcopy declaration completely
        new_lines = [line for line in lines if "void" not in line or "bcopy" not in line]
        os_libc.write_text('\n'.join(new_lines))
        print("Truncated bcopy from os_libc.h")

    # B. Fix gbi.h (The uSprite, Light, Hilite, and Gfx redefinitions)
    gbi = pr_dir / "gbi.h"
    if gbi.exists():
        content = gbi.read_text(errors='ignore')
        # Ruthlessly remove these specific blocks
        content = re.sub(r'typedef\s+union\s*\{[^}]*\}\s*uSprite\s*;', '/* uSprite bridged */', content, flags=re.DOTALL)
        content = re.sub(r'typedef\s+struct\s*\{[^}]*\}\s*Light_t\s*;', '/* Light_t bridged */', content, flags=re.DOTALL)
        content = re.sub(r'typedef\s+struct\s*\{[^}]*\}\s*Hilite_t\s*;', '/* Hilite_t bridged */', content, flags=re.DOTALL)
        content = re.sub(r'typedef\s+struct\s*\{[^}]*\}\s*Light\s*;', '/* Light bridged */', content, flags=re.DOTALL)
        content = re.sub(r'typedef\s+struct\s*\{[^}]*\}\s*Hilite\s*;', '/* Hilite bridged */', content, flags=re.DOTALL)
        content = re.sub(r'typedef\s+union\s*\{[^}]*\}\s*Gfx\s*;', '/* Gfx bridged */', content, flags=re.DOTALL)
        gbi.write_text(content)
        print("Truncated types from gbi.h")

    # C. Fix setintmask.cpp (Language linkage issue)
    setintmask = root / "Android/app/src/main/cpp/ultra/setintmask.cpp"
    if setintmask.exists():
        content = setintmask.read_text(errors='ignore')
        if 'extern "C"' not in content and 'osSetIntMask' in content:
             content = content.replace('OSIntMask osSetIntMask(OSIntMask mask)', 'extern "C" OSIntMask osSetIntMask(OSIntMask mask)')
             setintmask.write_text(content)
             print("Fixed language linkage in setintmask.cpp")

    # 4. Global Source Repair
    for path in root.rglob("*.[ch]*"):
        if "n64_types.h" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            content = content.replace('tools/rare_decompression.h', 'rare_decompression.h')
            content = content.replace('sched_yield()', 'n64_yield()')
            path.write_text(content)
        except: continue

if __name__ == "__main__":
    perform_precision_strike()
