#!/usr/bin/env python3
import re
import os
from pathlib import Path

def setup_harmonized_environment():
    cwd = Path.cwd().resolve()
    decomp_root = cwd / "decomp-files"
    include_dir = decomp_root / "include"
    sdk_dir = include_dir / "2.0L" / "PR"
    
    print(f"--- [v84.9] Harmonizing Symbols for AArch64 ---")

    # 1. THE COMPLETE BRIDGE: n64_types.h
    # Added Audio Command Macros (A_*) and OS Interrupt Macros (OS_IM_*)
    bridge_h = include_dir / "n64_types.h"
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

// SDK Guards
#define __OS_THREAD_H__
#define __OS_MESSAGE_H__
#define __OS_CONT_H__
#define _GBI_H_
#define _MBI_H_
#define _ABI_H_
#define _GU_H_

// OS Stubs & Types
typedef s32  OSPri;
typedef s32  OSId;
typedef void* OSMesg;
typedef struct { uint8_t d[48];  } OSMesgQueue;
typedef struct { uint8_t d[128]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;
typedef struct { uint8_t d[32];  } OSViMode;

// OS Macros & Stubs
#define OS_IM_NONE 0
typedef u32 OSIntMask;
static inline u32 osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }
static inline OSIntMask osGetIntMask(void) { return 0; }
static inline void osSetIntMask(OSIntMask m) { (void)m; }

// Audio Command Macros (Required for env.c and synth.c)
#define A_INIT      0x01
#define A_CONTINUE  0x02
#define A_MAIN      0x04
#define A_AUX       0x08
#define A_VOL       0x10
#define A_RATE      0x20
#define A_LEFT      0x40
#define A_RIGHT     0x80

// Graphics & Audio Opaque Types
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

    # 2. Neutralize SDK Headers (Directing them all to our bridge)
    toxic_list = [
        "ultratypes.h", "abi.h", "mbi.h", "gbi.h", "os_libc.h", 
        "os_thread.h", "os_message.h", "os_cont.h", "os.h", "gu.h"
    ]
    for name in toxic_list:
        target = sdk_dir / name
        if target.exists():
            target.write_text("#include <n64_types.h>\n")

    # 3. GLOBAL SOURCE PASS (Final 64-bit Pointer alignment)
    for path in decomp_root.rglob("*.[ch]"):
        if "PR/" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            # Final patch for any missed truncation issues
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            path.write_text(content)
        except: pass

    print(f"--- Harmonization v84.9 Complete ---")

if __name__ == "__main__":
    setup_harmonized_environment()
