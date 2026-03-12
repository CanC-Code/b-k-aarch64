#!/usr/bin/env python3
import re
import os
from pathlib import Path

def setup_harmonized_environment():
    cwd = Path.cwd().resolve()
    decomp_root = cwd / "decomp-files"
    include_dir = decomp_root / "include"
    sdk_dir = include_dir / "2.0L" / "PR"
    
    print(f"[>] Harmonizing Environment v84.3 at: {decomp_root}")

    # 1. The Ultra-Bridge (n64_types.h)
    # This now contains every missing "OS" and "AL" type found in your error log.
    bridge_content = """#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// Primitives
typedef uint8_t u8;   typedef int8_t s8;
typedef uint16_t u16; typedef int16_t s16;
typedef uint32_t u32; typedef int32_t s32;
typedef uint64_t u64; typedef int64_t s64;
typedef float f32;    typedef double f64;
typedef volatile uint32_t vu32;

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

// N64 OS Stubs (Required for main.h, pfsmanager.h, vimgr.h)
typedef s32  OSPri;
typedef s32  OSId;
typedef void* OSMesg;
typedef struct { u8 d[48]; } OSMesgQueue;
typedef struct { u8 d[128]; } OSThread;
typedef struct { u8 d[64]; } OSContPad;
typedef struct { u8 d[32]; } OSViMode;

// Graphics & Audio Opaque Types
typedef uint64_t Gfx;
typedef uint64_t Acmd;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { u8 d[16]; } Vtx;
typedef struct { u8 d[32]; } LookAt;
typedef struct { u8 d[32]; } Hilite;
typedef struct { u8 d[32]; } Light;
typedef struct { u8 d[64]; } uSprite;
typedef struct { u8 d[64]; } PositionalLight;

// Audio State Stubs (Fixes synthInternals.h errors)
typedef struct { u8 d[16]; } _SH_ALHeap;
#define ALHeap _SH_ALHeap
typedef struct { u8 d[64]; } Aadpcm;
typedef struct { u8 d[128]; } ADPCM_STATE;
typedef struct { u8 d[128]; } RESAMPLE_STATE;
typedef struct { u8 d[128]; } POLEF_STATE;
typedef struct { u8 d[128]; } ENVMIX_STATE;
typedef struct { u8 d[64]; } ALSeqFile;
typedef struct { u8 d[64]; } ALWaveTable;
typedef struct { u8 d[64]; } ALCSPlayer;

#define AL_ADPCM_WAVE 0
#define AL_SEQP_MIDI_EVT 0

#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

#endif
"""
    bridge_h = include_dir / "n64_types.h"
    bridge_h.write_text(bridge_content)

    # 2. Kill the 'bool' redefinition in bool.h
    bool_h = include_dir / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#ifndef _BOOL_H_\\n#define _BOOL_H_\\n#include <stdbool.h>\\n#endif\\n")

    # 3. Neutralize SDK Headers
    toxic = ["ultratypes.h", "abi.h", "mbi.h", "gbi.h", "os_libc.h", "gu.h", "os.h"]
    for name in toxic:
        target = sdk_dir / name
        if target.exists():
            target.write_text("#include <n64_types.h>\\n")

    # 4. Patch libaudio.h to use our proxy name for ALHeap
    libaudio = sdk_dir / "libaudio.h"
    if libaudio.exists():
        c = libaudio.read_text(errors='ignore')
        c = c.replace("} ALHeap;", "} _SH_AL_SDK_Heap;") # Rename the SDK's version
        libaudio.write_text(c)

if __name__ == "__main__":
    setup_harmonized_environment()
