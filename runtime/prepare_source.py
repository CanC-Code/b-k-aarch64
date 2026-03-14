import os
import re
from pathlib import Path

BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>

/** 1. N64 PRIMITIVES (Must be first to satisfy legacy headers) **/
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;

/** 2. HARDWARE / OS TYPES **/
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

/** 3. SYSTEM INCLUDES (Bypassing sched.h to break the loop) **/
#ifdef __cplusplus
  #include <cstring>
  #include <cstdlib>
  #include <cstdio>
  #include <ctime>
  extern "C" {
      int sched_yield(void); // Manually declared to prevent <sched.h> shadowing
  }
#else
  #include <string.h>
  #include <stdlib.h>
  #include <stdio.h>
  #include <time.h>
  extern int sched_yield(void);
#endif

/** 4. ANDROID SHIMS **/
#undef bcopy
#define bcopy(src, dst, n) memmove(dst, src, n)
static inline int n64_yield(void) { return sched_yield(); }

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#endif // _N64_TYPES_H_
"""

def deploy_smart_transformation():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- DEPLOYING SMART IN-FILL ENGINE ---")
    
    # 1. Deploy the self-sufficient bridge
    (include_dir / "n64_types.h").write_text(BRIDGE_CONTENT)

    # 2. NEUTRALIZE shadow clashing headers
    # This completely stops the NDK from breaking when it looks for <math.h>
    shadows = ["string.h", "bool.h", "time.h", "sched.h", "math.h", "malloc.h"]
    for s in shadows:
        p = include_dir / s
        if p.exists():
            print(f"Neutralizing shadow header: {s}")
            p.rename(p.with_suffix(".bak"))

    # 3. DYNAMIC IN-FILL (The Bulldozer)
    # We scan all files and comment out ONLY the specific typedefs causing redefinition errors.
    targets = ['OSTask', 'ALHeap', 'LookAt', 'Hilite', 'Light', 'Mtx', 'MtxF', 'OSThread', 'OSMesgQueue', 'OSMesg']
    
    for path in root.rglob("*.[ch]*"):
        if "n64_types.h" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Fix paths and yields
            content = content.replace('tools/rare_decompression.h', 'rare_decompression.h')
            content = content.replace('sched_yield()', 'n64_yield()')
            
            # Regex Bulldozer: Safely removes `typedef struct/union ... Target;`
            for t in targets:
                # Match full struct/union blocks
                pattern = r'typedef\s+(struct|union)\s*([^{;]*?\{[^}]*?\}|[^{;]+?)\s*' + t + r'\s*;'
                content = re.sub(pattern, f'/* {t} bridged */', content, flags=re.DOTALL)
                
                # Match direct pointer typedefs (like `typedef void * OSMesg;`)
                pattern2 = r'typedef\s+[a-zA-Z_][a-zA-Z0-9_\s\*]+?\s*' + t + r'\s*;'
                content = re.sub(pattern2, f'/* {t} pointer bridged */', content)

            if content != original:
                path.write_text(content)
        except: continue

if __name__ == "__main__":
    deploy_smart_transformation()
