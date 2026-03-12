#!/usr/bin/env python3
import re
import os
from pathlib import Path

def setup_harmonized_environment():
    cwd = Path.cwd().resolve()
    decomp_root = cwd / "decomp-files"
    include_dir = decomp_root / "include"
    sdk_dir = include_dir / "2.0L" / "PR"
    
    print(f"[>] Harmonizing Environment v84.5")

    # 1. The Clean Bridge (n64_types.h)
    # We remove the audio stubs so libaudio.h can define them properly.
    bridge_content = """#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

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

// OS Stubs
typedef s32 OSPri;
typedef s32 OSId;
typedef void* OSMesg;
typedef struct { uint8_t d[48]; } OSMesgQueue;
typedef struct { uint8_t d[128]; } OSThread;
typedef struct { uint8_t d[64]; } OSContPad;

// Graphics Opaque Types (Safe to keep as stubs)
typedef uint64_t Gfx;
typedef uint64_t Acmd;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[16]; } Vtx;

#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif
#endif
"""
    (include_dir / "n64_types.h").write_text(bridge_content)

    # 2. Hard-Fix bool.h (Delete the redefinition)
    bool_h = include_dir / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#pragma once\n#include <stdbool.h>\n")

    # 3. Precision SDK Patching
    # We DO NOT blackhole libaudio.h or gu.h because the game needs their contents.
    # We only blackhole the low-level hardware headers.
    toxic = ["ultratypes.h", "abi.h", "mbi.h", "gbi.h", "os_libc.h"]
    for name in toxic:
        target = sdk_dir / name
        if target.exists():
            target.write_text("#include <n64_types.h>\n")

    # 4. Fix libaudio.h (Remove ONLY the clashing ALHeap)
    libaudio = sdk_dir / "libaudio.h"
    if libaudio.exists():
        c = libaudio.read_text(errors='ignore')
        # If ALHeap is already in n64_types, we must hide it here
        if "typedef struct {\\n    u8          *base;" in c:
            c = c.replace("typedef struct {", "#ifndef _ALHEAP_DONE_\ntypedef struct {", 1)
            c = c.replace("} ALHeap;", "} ALHeap;\\n#endif", 1)
        libaudio.write_text(f"#define _AL_HIDDEN_\\n{c}")

    # 5. Fix (u32) pointer casts in all source files
    for path in decomp_root.rglob("*.[ch]"):
        if "PR/" in str(path): continue
        content = path.read_text(errors='ignore')
        if "(u32)" in content:
            # Change (u32)ptr to (u32)(uintptr_t)ptr to satisfy 64-bit Clang
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            path.write_text(content)

if __name__ == "__main__":
    setup_harmonized_environment()
