#!/usr/bin/env python3
import re
import os
from pathlib import Path

def setup_harmonized_environment():
    cwd = Path.cwd().resolve()
    decomp_root = cwd / "decomp-files"
    include_dir = decomp_root / "include"
    sdk_dir = include_dir / "2.0L" / "PR"
    
    print(f"--- [v84.7] Harmonizing Banjo-Kazooie for AArch64 ---")

    # 1. AUTO-CREATION: n64_types.h
    # We write this to the include folder to ensure it's the first thing Clang sees.
    bridge_h = include_dir / "n64_types.h"
    bridge_content = """#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// 1. Basic Primitives (Architecture Independent)
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

// 2. SDK Guards: Pre-emptively "locking" SDK files to stop redefinitions
#define __OS_THREAD_H__
#define __OS_MESSAGE_H__
#define __OS_CONT_H__
#define _GBI_H_
#define _MBI_H_
#define _ABI_H_

// 3. OS Stubs (Sized for BK struct compatibility)
typedef s32  OSPri;
typedef s32  OSId;
typedef void* OSMesg;
typedef struct { uint8_t d[48];  } OSMesgQueue;
typedef struct { uint8_t d[128]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;
typedef struct { uint8_t d[32];  } OSViMode;

// 4. Graphics & Audio Opaque Types
typedef uint64_t Gfx;
typedef uint64_t Acmd;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[16];  } Vtx;
typedef struct { uint8_t d[32];  } LookAt;
typedef struct { uint8_t d[32];  } Hilite;
typedef struct { uint8_t d[32];  } Light;
typedef struct { uint8_t d[64];  } uSprite;
typedef struct { uint8_t d[64];  } PositionalLight;

typedef struct { uint8_t d[128]; } ADPCM_STATE;
typedef struct { uint8_t d[128]; } RESAMPLE_STATE;
typedef struct { uint8_t d[128]; } POLEF_STATE;
typedef struct { uint8_t d[128]; } ENVMIX_STATE;

#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif
#endif
"""
    bridge_h.write_text(bridge_content)
    print(f"[+] Created/Updated: {bridge_h}")

    # 2. AUTO-FIX: bool.h
    # This kills the "cannot combine with previous int" error.
    bool_h = include_dir / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#ifndef _BOOL_H_\n#define _BOOL_H_\n#include <stdbool.h>\n#endif\n")
        print(f"[+] Sanitized: {bool_h}")

    # 3. BLACKHOLE: Toxic SDK Headers
    # We replace their contents with a single include to our bridge.
    toxic_list = [
        "ultratypes.h", "abi.h", "mbi.h", "gbi.h", "os_libc.h", 
        "os_thread.h", "os_message.h", "os_cont.h", "os.h"
    ]
    for name in toxic_list:
        target = sdk_dir / name
        if target.exists():
            target.write_text("#include <n64_types.h>\n")
            print(f"[!] Neutralized SDK Header: {name}")

    # 4. SURGERY: libaudio.h
    # Removes the duplicate ADPCM_STATE that Clang hates.
    libaudio = sdk_dir / "libaudio.h"
    if libaudio.exists():
        c = libaudio.read_text(errors='ignore')
        c = re.sub(r"typedef struct \{.*?\} ADPCM_STATE;", "/* SH-STUB */", c, flags=re.DOTALL)
        libaudio.write_text(c)
        print(f"[+] Cleaned up libaudio.h redefinitions")

    # 5. GLOBAL REPAIR: Pointers and Includes
    # We iterate through every file to fix (u32)ptr truncation and string.h collisions.
    for path in decomp_root.rglob("*.[ch]"):
        if "PR/" in str(path): continue # Don't touch our neutralized SDK
        try:
            raw = path.read_text(errors='ignore')
            # 5a. Fix Include collision
            content = raw.replace('"string.h"', '<string.h>')
            # 5b. Fix 64-bit Pointer Truncation
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            if content != raw:
                path.write_text(content)
                print(f"[*] Repaired: {path.relative_to(decomp_root)}")
        except Exception as e:
            print(f"[X] Could not process {path.name}: {e}")

    print(f"--- Harmonization Complete. Ready for Ninja Build ---")

if __name__ == "__main__":
    setup_harmonized_environment()
