import os
import re
from pathlib import Path

# THE ATOMIC BRIDGE: Precise types for AArch64 satisfaction
BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>

/** 1. N64 PRIMITIVES - Defined FIRST so headers like sched.h can use them **/
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;

typedef s32 OSPri;
typedef s32 OSId;
typedef void* OSTask;
typedef void* ALHeap;
typedef void* OSMesg;

/** 2. CORE STRUCTURES **/
typedef struct { void* mt; void* full; int32_t count; } OSMesgQueue;

typedef struct { uint32_t status; uint32_t pc; uint64_t regs[32]; } OSContext;
typedef struct OSThread_s {
    struct OSThread_s *next;
    int32_t           priority;
    OSContext         context;
    uint8_t           stack_padding[128];
} OSThread;

typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;

/** 3. SYSTEM INCLUDES - Forced first for namespace safety **/
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
    static inline int n64_yield(void) { return sched_yield(); }

// Redirect bcopy to fix Android macro conflict
#undef bcopy
#define bcopy(src, dst, n) memmove(dst, src, n)

/** 4. THE BLOCKADE **/
#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _GBI_H_
#define _OS_H_
#define _OS_THREAD_H_
#define _OS_MESSAGE_H_
#define _OS_LIBC_H_
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

def deploy_adaptive_transformation():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- DEPLOYING ADAPTIVE TRANSFORMATION ---")
    
    # 1. Update the bridge
    (include_dir / "n64_types.h").write_text(BRIDGE_CONTENT)

    # 2. NEUTRALIZE shadow clashing headers (Shadow protection)
    # Renaming them forces NDK to find system versions
    clashes = ["string.h", "bool.h", "time.h", "sched.h"]
    for c in clashes:
        p = include_dir / c
        if p.exists():
            new_p = include_dir / f"n64_sys_{c}"
            print(f"Neutralizing shadow: {c} -> {new_p.name}")
            p.rename(new_p)

    # 3. ADAPTIVE IN-FILL: Replace legacy SDK content with our bridge pointer
    # This prevents 'redefinition' while providing the 'u32' etc. needed for sched.h
    legacy_pr = include_dir / "2.0L" / "PR"
    if legacy_pr.exists():
        for header in ["os_thread.h", "os_message.h", "os_libc.h", "gbi.h", "ultra64.h"]:
            target = legacy_pr / header
            if target.exists():
                print(f"Adapting legacy header: {header}")
                target.write_text("#include \"n64_types.h\"\n")

    # 4. GLOBAL SOURCE SCAN & REPAIR
    for path in root.rglob("*.[ch]*"):
        if "n64_types.h" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Fix sched_yield calls across the project
            content = content.replace('sched_yield()', 'n64_yield()')
            
            # Normalize rare_decompression paths
            content = content.replace('tools/rare_decompression.h', 'rare_decompression.h')
            
            # Remove local OSThread definitions (Satisfaction already provided by bridge)
            content = re.sub(r'typedef struct OSThread_s\s*\{.*?\}\s*OSThread\s*;', '/* Ref Bridge */', content, flags=re.DOTALL)

            if content != original:
                path.write_text(content)
        except: continue

if __name__ == "__main__":
    deploy_adaptive_transformation()
