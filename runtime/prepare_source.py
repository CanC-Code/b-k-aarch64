#!/usr/bin/env python3
import re
import os
from pathlib import Path

def setup_harmonized_environment():
    cwd = Path.cwd().resolve()
    decomp_root = cwd / "decomp-files"
    include_dir = decomp_root / "include"
    sdk_dir = include_dir / "2.0L" / "PR"
    
    print(f"[>] Harmonizing Environment v84.4 at: {decomp_root}")

    # 1. The Ultra-Bridge (n64_types.h)
    # Provides stubs for the OS and Audio types we "removed" from the SDK.
    bridge_content = """#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// Standard N64 Primitives
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
typedef struct { uint8_t d[48]; } OSMesgQueue;
typedef struct { uint8_t d[128]; } OSThread;
typedef struct { uint8_t d[64]; } OSContPad;
typedef struct { uint8_t d[32]; } OSViMode;

// Graphics & Audio Opaque Types
typedef uint64_t Gfx;
typedef uint64_t Acmd;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[16]; } Vtx;
typedef struct { uint8_t d[32]; } LookAt;
typedef struct { uint8_t d[32]; } Hilite;
typedef struct { uint8_t d[32]; } Light;
typedef struct { uint8_t d[64]; } uSprite;
typedef struct { uint8_t d[64]; } PositionalLight;

// Audio State Stubs
typedef struct { uint8_t d[16]; } _SH_ALHeap;
#define ALHeap _SH_ALHeap
typedef struct { uint8_t d[64]; } Aadpcm;
typedef struct { uint8_t d[128]; } ADPCM_STATE;
typedef struct { uint8_t d[128]; } RESAMPLE_STATE;
typedef struct { uint8_t d[128]; } POLEF_STATE;
typedef struct { uint8_t d[128]; } ENVMIX_STATE;
typedef struct { uint8_t d[64]; } ALSeqFile;
typedef struct { uint8_t d[64]; } ALWaveTable;
typedef struct { uint8_t d[64]; } ALCSPlayer;

#define AL_ADPCM_WAVE 0
#define AL_SEQP_MIDI_EVT 0

#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

#endif
"""
    (include_dir / "n64_types.h").write_text(bridge_content)

    # 2. Fix the 'bool' conflict in bool.h
    bool_h = include_dir / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#ifndef _BOOL_H_\n#define _BOOL_H_\n#include <stdbool.h>\n#endif\n")

    # 3. Blackhole the Toxic SDK Headers
    toxic = ["ultratypes.h", "abi.h", "mbi.h", "gbi.h", "os_libc.h", "gu.h", "os.h"]
    for name in toxic:
        target = sdk_dir / name
        if target.exists():
            target.write_text("#include <n64_types.h>\n")

    # 4. Global Source Cleanup (Pointer safety & includes)
    for path in decomp_root.rglob("*.[ch]"):
        if "PR/" in str(path): continue
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            # Use system string library
            content = content.replace('"string.h"', '<string.h>')
            # Fix 64-bit pointer truncation: (u32)ptr -> (u32)(uintptr_t)ptr
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            path.write_text(content)
        except Exception as e:
            print(f"Skipping {path.name}: {e}")

if __name__ == "__main__":
    setup_harmonized_environment()
