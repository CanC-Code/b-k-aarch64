import os
import re
from pathlib import Path

# THE ANATOMICAL BRIDGE: Provides real members so logic doesn't break.
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

/** 2. ANATOMICAL MOCKS - Replacing byte arrays with real members **/
typedef struct OSThread_s {
    struct OSThread_s *next;
    int32_t           priority;
    struct {
        uint32_t status;
        uint32_t pc;
        uint64_t regs[32];
    } context;
    uint8_t           stack_padding[128];
} OSThread;

typedef void* OSMesg;
typedef struct OSMesgQueue_s {
    void* mt;
    void* full;
    int32_t count;
} OSMesgQueue;

typedef struct {
    uint16_t button;
    int8_t   stick_x;
    int8_t   stick_y;
    uint8_t  errno;
} OSContPad;

typedef uint32_t OSId;
typedef uint32_t OSPri;
typedef uint64_t OSTime;
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { int16_t ob[3]; uint16_t flag; int16_t tc[2]; uint8_t cn[4]; } Vtx_t;
typedef union { Vtx_t v; long long force_align; } Vtx;

/** 3. MACRO BLOCKADE - Add libaudio to the list **/
#define _ULTRATYPES_H_
#define __OS_H__
#define _OS_H_
#define _OS_THREAD_H_
#define _OS_MESSAGE_H_
#define _OS_CONT_H_
#define _OS_LIBC_H_
#define _GBI_H_
#define _ULTRA64_H_
#define _LIBAUDIO_H_
#define _AL_H_

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

typedef void* ALHeap;
typedef void* OSTask;

#endif // _N64_TYPES_H_
"""

def deploy_anatomical_patch():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v181.0] DEPLOYING ANATOMICAL MOCK PATCH ---")
    
    # 1. Update the Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. SURGERY: exceptasm.cpp contains a local redefinition of OSThread
    exceptasm = root / "Android/app/src/main/cpp/ultra/exceptasm.cpp"
    if exceptasm.exists():
        text = exceptasm.read_text()
        # Remove local 'typedef struct OSThread_s' blocks to defer to the bridge
        text = re.sub(r'typedef struct OSThread_s\s*\{.*?\}\s*OSThread\s*;', '/* Use bridge OSThread */', text, flags=re.DOTALL)
        # Fix nullptr/NULL usage for C++
        text = text.replace('NULL', 'nullptr')
        exceptasm.write_text(text)

    # 3. Suppress project headers that are now handled by the bridge
    targets = ["structs.h", "model.h"]
    for t in targets:
        p = include_dir / t
        if p.exists():
            content = p.read_text(errors='ignore')
            # Remove any line that defines Mtx, MtxF, or Vtx to avoid redefinitions
            content = re.sub(r'typedef struct\s*\{.*?\}\s*(MtxF|Mtx)\s*;', '/* Defined in bridge */', content, flags=re.DOTALL)
            p.write_text(content)

    # 4. Total Wipe of libaudio.h to stop the audio redefinitions
    libaudio = include_dir / "2.0L/PR/libaudio.h"
    if libaudio.exists():
        libaudio.write_text("#include \"n64_types.h\"\n/* Libaudio content moved to bridge mocks */\n")

if __name__ == "__main__":
    deploy_anatomical_patch()
