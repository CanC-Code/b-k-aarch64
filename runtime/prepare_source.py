import os
import re
from pathlib import Path

# THE ANATOMICAL BRIDGE: Provides the full structure the engine expects.
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

/** 2. ANATOMICAL MOCKS - Real members for exceptasm.cpp **/
typedef struct {
    uint32_t status;
    uint32_t pc;
    uint64_t regs[32];
} OSContext;

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

/** 3. PROJECT MACROS **/
#define PAIR(type, name) type name[2]
#define TUPLE(type, name) type name[3]
#define TUPLE_PAIR(type, name) type name[2][3]
#define FREE_LIST(type) struct { struct type *head; int32_t count; }

/** 4. SYSTEM PROTECTION **/
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
    // Shim for the problematic sched_yield call in NDK headers
    #include <sched.h>
#ifdef __cplusplus
  }
#endif

#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _BOOL_H_
#define _TIME_H_
#define _SCHED_H_

typedef void* ALHeap;
typedef void* OSTask;

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#endif // _N64_TYPES_H_
"""

def deploy_lockdown():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v185.0] DEPLOYING TOTAL LOCKDOWN ---")
    
    # 1. Neutralize Clashing Headers
    # Rename to prevent the NDK from picking project versions of system headers
    clashes = ["string.h", "bool.h", "time.h", "sched.h"]
    for c in clashes:
        p = include_dir / c
        if p.exists():
            new_p = include_dir / f"n64_{c}"
            print(f"Locking {c} -> {new_p.name}")
            p.rename(new_p)

    # 2. Deploy anatomical bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 3. SURGERY: Cleanup exceptasm.cpp
    # Remove the local OSThread_s definition that's causing redefinition errors
    asm_cpp = root / "Android/app/src/main/cpp/ultra/exceptasm.cpp"
    if asm_cpp.exists():
        text = asm_cpp.read_text()
        text = re.sub(r'typedef struct OSThread_s\s*\{.*?\}\s*OSThread\s*;', '/* Use bridge anatomy */', text, flags=re.DOTALL)
        asm_cpp.write_text(text)

    # 4. Path Fix: resource_mgr.cpp
    res_cpp = root / "Android/app/src/main/cpp/emulator/resource_mgr.cpp"
    if res_cpp.exists():
        text = res_cpp.read_text()
        text = text.replace('#include "tools/rare_decompression.h"', '#include "rare_decompression.h"')
        res_cpp.write_text(text)

if __name__ == "__main__":
    deploy_lockdown()
