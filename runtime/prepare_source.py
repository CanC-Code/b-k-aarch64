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

/** 3. PROJECT MACROS **/
#define PAIR(type, name) type name[2]
#define TUPLE(type, name) type name[3]
#define TUPLE_PAIR(type, name) type name[2][3]
#define FREE_LIST(type) struct { struct type *head; int32_t count; }

/** 4. SYSTEM & BLOCKADE **/
#ifdef __cplusplus
  #include <cstring>
  #include <cstdlib>
  #include <cstdio>
  #include <ctime>
  #include <sched.h>
  extern "C" {
    static inline int sched_yield_compat(void) { return sched_yield(); }
#else
  #include <string.h>
  #include <stdlib.h>
  #include <stdio.h>
  #include <time.h>
  #include <sched.h>
  static inline int sched_yield_compat(void) { return sched_yield(); }
#endif

#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _GBI_H_
#define _OS_H_
#define _OS_THREAD_H_
#define _OS_MESSAGE_H_
#define _OS_LIBC_H_
#define _BOOL_H_
#define _TIME_H_

typedef void* ALHeap;
typedef void* OSTask;
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

def deploy_isolation():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v186.0] DEPLOYING TOTAL ISOLATION ---")
    
    # 1. Rename clashing headers to stop shadowing system libraries
    clashes = ["string.h", "bool.h", "time.h", "sched.h"]
    for c in clashes:
        p = include_dir / c
        if p.exists():
            new_p = include_dir / f"n64_{c}"
            p.rename(new_p)

    # 2. Deploy the new bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 3. Patch exceptasm.cpp (Remove redefinition)
    asm_cpp = root / "Android/app/src/main/cpp/ultra/exceptasm.cpp"
    if asm_cpp.exists():
        text = asm_cpp.read_text()
        text = re.sub(r'typedef struct OSThread_s\s*\{.*?\}\s*OSThread\s*;', '/* Bridge-defined */', text, flags=re.DOTALL)
        asm_cpp.write_text(text)

    # 4. Patch NativeBridge.cpp (Fix alGlobals conflict)
    nb_cpp = root / "Android/app/src/main/cpp/ultra/NativeBridge.cpp"
    if nb_cpp.exists():
        text = nb_cpp.read_text()
        text = text.replace('ALGlobals *alGlobals = NULL;', 'ALGlobals *alGlobals = nullptr;')
        nb_cpp.write_text(text)

    # 5. Global sched_yield swap
    for path in root.rglob("*.[ch]*"):
        if "n64_types.h" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            if "sched_yield()" in content:
                path.write_text(content.replace("sched_yield()", "sched_yield_compat()"))
        except: continue

if __name__ == "__main__":
    deploy_isolation()
