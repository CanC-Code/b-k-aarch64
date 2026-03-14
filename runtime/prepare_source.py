import os
import re
from pathlib import Path

# THE ATOMIC BRIDGE: The single source of truth for N64 types on Android.
BASE_BRIDGE_CONTENT = r"""
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

/** 2. ANATOMICAL MOCKS **/
typedef struct { uint32_t status; uint32_t pc; uint64_t regs[32]; } OSContext;
typedef struct OSThread_s {
    struct OSThread_s *next;
    int32_t           priority;
    OSContext         context;
    uint8_t           stack_padding[128];
} OSThread;

typedef void* OSMesg;
typedef struct { void* mt; void* full; int32_t count; } OSMesgQueue;

typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { int16_t ob[3]; uint16_t flag; int16_t tc[2]; uint8_t cn[4]; } Vtx_t;
typedef union { Vtx_t v; long long force_align; } Vtx;

/** 3. C++ COMPATIBILITY & SYSTEM HEADERS **/
#ifdef __cplusplus
  #include <cstring>
  #include <cstdlib>
  #include <cstdio>
  extern "C" {
#else
  #include <string.h>
  #include <stdlib.h>
  #include <stdio.h>
#endif

// Prevent legacy headers from ever loading
#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _GBI_H_
#define _OS_H_
#define _OS_THREAD_H_
#define _OS_MESSAGE_H_
#define _OS_LIBC_H_
#define _BOOL_H_

typedef void* ALHeap;
typedef void* OSTask;

#ifdef __cplusplus
}
#endif

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#endif // _N64_TYPES_H_
"""

def deploy_nuclear_neutralization():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v193.0] DEPLOYING NUCLEAR NEUTRALIZATION ---")
    
    # 1. Update the Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. NEUTRALIZE conflicting project headers
    # We rename them so the NDK finds system headers (like string.h) instead.
    conflicts = ["string.h", "bool.h", "time.h", "sched.h"]
    for c in conflicts:
        p = include_dir / c
        if p.exists():
            print(f"Neutralizing local {c} to prevent system shadowing.")
            p.rename(p.with_suffix(".h.bak"))

    # 3. SURGICALLY EMPTY legacy SDK headers
    # This stops the "typedef redefinition" errors from 2.0L/PR
    legacy_pr_path = include_dir / "2.0L" / "PR"
    if legacy_pr_path.exists():
        for h in ["os_thread.h", "os_message.h", "gbi.h", "os_libc.h", "ultra64.h"]:
            target = legacy_pr_path / h
            if target.exists():
                print(f"Emptying legacy header: {h}")
                target.write_text("#include \"n64_types.h\"\n")

    # 4. FIX: structs.h redefinition of MtxF
    structs_h = include_dir / "structs.h"
    if structs_h.exists():
        text = structs_h.read_text(errors='ignore')
        # Remove the local MtxF/Mtx definitions that clash with the bridge
        text = re.sub(r'typedef struct\s*\{.*?\}\s*(MtxF|Mtx)\s*;', '/* Ref in bridge */', text, flags=re.DOTALL)
        structs_h.write_text(text)

    # 5. Fix exceptasm.cpp redefinition
    asm_cpp = root / "Android/app/src/main/cpp/ultra/exceptasm.cpp"
    if asm_cpp.exists():
        text = asm_cpp.read_text()
        text = re.sub(r'typedef struct OSThread_s\s*\{.*?\}\s*OSThread\s*;', '/* Ref in bridge */', text, flags=re.DOTALL)
        asm_cpp.write_text(text)

if __name__ == "__main__":
    deploy_nuclear_neutralization()
