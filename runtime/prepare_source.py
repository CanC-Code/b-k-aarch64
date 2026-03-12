#!/usr/bin/env python3
import re
import os
from pathlib import Path

def setup_harmonized_environment():
    # 1. Dynamic Path Discovery
    cwd = Path.cwd()
    decomp_root = cwd / "decomp-files"
    include_dir = decomp_root / "include"
    sdk_dir = include_dir / "2.0L" / "PR"
    
    print(f"[>] Harmonizing Environment at: {decomp_root}")
    include_dir.mkdir(parents=True, exist_ok=True)

    # 2. Create the Master Bridge (n64_types.h)
    # This file satisfies every conflict we've discovered so far.
    bridge_content = """#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// Standard N64 Primitives (Fixed for ARM64)
typedef uint8_t u8;   typedef int8_t s8;
typedef uint16_t u16; typedef int16_t s16;
typedef uint32_t u32; typedef int32_t s32;
typedef uint64_t u64; typedef int64_t s64;
typedef float f32;    typedef double f64;
typedef volatile uint32_t vu32; typedef volatile int32_t vs32;

#ifndef TRUE
  #define TRUE true
  #define FALSE false
#endif

// Hardware Alignment & Opaque Types
typedef struct { uint32_t w0; uint32_t w1; } Awords;
typedef struct { uint32_t w0; uint32_t w1; } Apolef;
typedef uint64_t Gfx;
typedef uint64_t Acmd;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { u8 d[16]; } Vtx;
typedef struct { u8 d[32]; } LookAt;
typedef struct { u8 d[32]; } Hilite;
typedef struct { u8 d[32]; } Light;
typedef struct { u8 d[64]; } uSprite;
typedef struct { u8 d[64]; } PositionalLight;

// Audio State Proxies
typedef struct { u8 d[16]; } ALHeap;
typedef struct { u8 d[64]; } Aadpcm;
typedef struct { u8 d[128]; } ADPCM_STATE;
typedef struct { u8 d[128]; } RESAMPLE_STATE;
typedef struct { u8 d[128]; } POLEF_STATE;
typedef struct { u8 d[128]; } ENVMIX_STATE;

// Redirect legacy memory functions to optimized ARM64 built-ins
#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

// Prevent N64 SDK from redefining our hard-won types
#define _ULTRA64_H_
#define _GU_H_
#define _ALHEAP_H_

bool audioManager_handleFrameMsg(void *info, void *prev_info);

#endif
"""
    (include_dir / "n64_types.h").write_text(bridge_content)

    # 3. Neutralize "Toxic" SDK Headers
    # We replace them with simple redirects to our bridge.
    toxic_list = ["ultratypes.h", "abi.h", "mbi.h", "gbi.h", "os_libc.h", "gu.h"]
    for name in toxic_list:
        target = sdk_dir / name
        if target.exists():
            target.write_text("#include <n64_types.h>\n")

    # 4. Fix libaudio.h (Remove the specific blocks that cause redefinition)
    libaudio = sdk_dir / "libaudio.h"
    if libaudio.exists():
        c = libaudio.read_text(errors='ignore')
        # Use regex to strip the conflicting structs entirely
        c = re.sub(r"typedef struct \{.*?\} (ALHeap|Aadpcm);", "/* SH-STUB */", c, flags=re.DOTALL)
        c = re.sub(r"typedef short ADPCM_STATE\[.*?\];", "/* SH-STUB */", c)
        libaudio.write_text(c)

    # 5. Global Source Cleanup
    # Fix 64-bit pointer truncation and local include collisions
    for path in decomp_root.rglob("*.[ch]"):
        if "PR/" in str(path): continue
        content = path.read_text(errors='ignore')
        # Ensure we use system strings, not local N64 ones
        content = content.replace('"string.h"', '<string.h>')
        # Fix: (u32)ptr -> (u32)(uintptr_t)ptr
        content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
        path.write_text(content)

if __name__ == "__main__":
    setup_harmonized_environment()
