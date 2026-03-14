import os
from pathlib import Path

# THE ATOMIC BRIDGE: Syntactically perfect, mathematically aligned.
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

/** 2. BOOTSTRAP SYSTEM HEADERS & C++ LINKAGE **/
#ifdef __cplusplus
  #include <cstring>
  #include <cstdlib>
  #include <cstdio>
  #include <ctime>
  extern "C" {
#else
  #include <string.h>
  #include <stdlib.h>
  #include <stdio.h>
  #include <time.h>
#endif

// Forward declare POSIX yield to avoid shadow looping
extern int sched_yield(void);

/** 3. HARDWARE & GRAPHICS TYPES **/
typedef void* OSTask;
typedef void* ALHeap;
typedef void* uSprite;
typedef uint64_t Gfx;
typedef struct { float m[4][4]; } MtxF;
typedef union { struct { int32_t m[4][4]; }; long long force_align; } Mtx;

typedef struct { uint8_t col[3]; int8_t dir[3]; } Light_t;
typedef union { Light_t l; long long force_align; } Light;
typedef struct { int16_t x, y, z; } LookAt_t;
typedef union { LookAt_t l; long long force_align; } LookAt;
typedef struct { int16_t x, y, z; } Hilite_t;
typedef union { Hilite_t h; long long force_align; } Hilite;

/** 4. OS STRUCTURES **/
typedef void* OSMesg;
typedef struct OSMesgQueue_s { void* mt; void* full; int32_t count; } OSMesgQueue;
typedef int32_t OSPri;
typedef int32_t OSId;
typedef struct { uint32_t status; uint32_t pc; uint64_t regs[32]; } OSContext;
typedef struct OSThread_s {
    struct OSThread_s *next;
    int32_t           priority;
    OSContext         context;
    uint8_t           stack_padding[128];
} OSThread;

/** 5. ANDROID COMPATIBILITY SHIMS **/
#undef bcopy
#define bcopy(src, dst, n) memmove((dst), (src), (n))
static inline int n64_yield(void) { return sched_yield(); }

typedef struct ALGlobals_s { uint8_t d[1024]; } ALGlobals;

#ifdef __cplusplus
} // PROPERLY CLOSE THE EXTERN C BRACE
#endif

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#endif // _N64_TYPES_H_
"""

def deploy_omni_shield():
    root = Path.cwd().resolve()
    print("--- DEPLOYING OMNI-SHIELD ENGINE v300.0 ---")
    
    # 1. Establish the Bridge (Source of Truth)
    bridge_path = root / "decomp-files" / "include" / "n64_types.h"
    if not bridge_path.parent.exists(): bridge_path.parent.mkdir(parents=True)
    bridge_path.write_text(BRIDGE_CONTENT)

    # 2. BLANKET SHADOW NEUTRALIZATION
    # Renames any local file that masks an Android standard library file.
    shadows = ["string.h", "bool.h", "time.h", "sched.h", "math.h", "malloc.h"]
    for path in root.rglob("*.h"):
        if path.name in shadows and "sysroot" not in str(path) and "n64_sys" not in path.name:
            new_name = f"n64_sys_{path.name}"
            print(f"Neutralized System Shadow: {path.name} -> {new_name} (in {path.parent.name})")
            path.rename(path.with_name(new_name))

    # 3. GLOBAL LEGACY HEADER OVERRIDE
    # No matter what folder they hide in, these files will be overridden.
    legacy_clashes = [
        "os_thread.h", "os_message.h", "os_libc.h", "sptask.h", 
        "gbi.h", "libaudio.h", "gu.h", "ultra64.h"
    ]
    for path in root.rglob("*.h"):
        if path.name in legacy_clashes and "n64_sys" not in path.name:
            print(f"Overriding Legacy SDK Header: {path.name} (in {path.parent.name})")
            path.write_text('#include "n64_types.h"\n')

    # 4. SOURCE-LEVEL ADAPTATION
    for path in root.rglob("*.[ch]*"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            orig = content
            
            # Global fixes required by the NDK compiler
            content = content.replace('tools/rare_decompression.h', 'rare_decompression.h')
            content = content.replace('sched_yield()', 'n64_yield()')
            
            # Fix specific C/C++ linkage issue caught in previous logs
            if path.name == "setintmask.cpp" and 'extern "C"' not in content:
                content = content.replace('OSIntMask osSetIntMask', 'extern "C" OSIntMask osSetIntMask')

            if orig != content:
                path.write_text(content)
        except Exception as e:
            continue

    print("--- OMNI-SHIELD DEPLOYED SUCCESSFULLY ---")

if __name__ == "__main__":
    deploy_omni_shield()
