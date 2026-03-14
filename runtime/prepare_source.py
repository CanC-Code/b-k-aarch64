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

/** 3. SYSTEM INCLUDES - Must load before blockades **/
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

// Block the legacy SDK headers
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

def deploy_anatomical_patch():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v192.0] DEPLOYING ANATOMICAL PATCH ---")
    
    # 1. Update the Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. SURGERY: exceptasm.cpp contains a local redefinition of OSThread
    asm_cpp = root / "Android/app/src/main/cpp/ultra/exceptasm.cpp"
    if asm_cpp.exists():
        text = asm_cpp.read_text()
        # Kill the local struct definition so it uses the bridge's version
        text = re.sub(r'typedef struct OSThread_s\s*\{.*?\}\s*OSThread\s*;', '/* Use Bridge */', text, flags=re.DOTALL)
        asm_cpp.write_text(text)

    # 3. GLOBAL PATH FIX: Fix the rare_decompression pathing in all files
    for path in root.rglob("*.[ch]*"):
        try:
            content = path.read_text(errors='ignore')
            if 'tools/rare_decompression.h' in content:
                print(f"Fixing path in {path.name}")
                path.write_text(content.replace('tools/rare_decompression.h', 'rare_decompression.h'))
        except: continue

if __name__ == "__main__":
    deploy_anatomical_patch()
