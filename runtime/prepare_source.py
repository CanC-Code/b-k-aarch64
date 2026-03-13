import os
import re
from pathlib import Path

BASE_BRIDGE_CONTENT = """
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// 1. Primitive Types
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

// 2. Hardware Structs (64-bit safe overrides)
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { uint8_t d[16]; } Vtx;
typedef struct { float d[16]; } BoneTransform;
typedef struct { BoneTransform *transforms; int count; } BoneTransformList;
typedef void* VLA; typedef void* FLA;
typedef struct { u32 t[16]; } OSTask_t;
typedef void (*OSErrorHandler)(void);
typedef struct { u32 d[16]; } OSLog;
typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;

typedef struct OSThread_s {
    struct OSThread_s *next; u32 priority;
    struct { u32 status; u32 pc; u32 sp; u32 d[16]; } context;
    uint8_t d[256]; 
} OSThread;

typedef struct { uint8_t d[64];  } OSContPad;
typedef struct { unsigned int w0, w1; } Acmd_words;
typedef union { Acmd_words words; long long force_align; } Acmd;
typedef s32 (*ALDMAproc)(s32 addr, s32 len, void *state);
typedef ALDMAproc (*ALDMANew)(void *state); // Fixed to void* to match SDK

typedef u32 OSIntMask;

// 3. System Standard Libraries (Pull from Android Sysroot)
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>

#if defined(__cplusplus)
#include <sched.h>
extern "C" int sched_yield(void);
#endif

// 4. Memory Mapper
#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

#endif // _N64_TYPES_H_
"""

def deploy_dynamic_patch():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    pr_folder = include_dir / "2.0L" / "PR"
    
    print("--- [v167.0] RUNNING SURGICAL LINKAGE FIXER ---")
    
    # 1. Write the Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. DELETE local clones of standard C headers to force usage of NDK headers
    # This prevents "no member named memcpy in global namespace"
    for sh in ["string.h", "math.h", "stdarg.h", "time.h", "stdio.h", "stdlib.h", "ctype.h", "basic_types.h"]:
        p = include_dir / sh
        if p.exists(): 
            print(f"Removing colliding header: {sh}")
            p.unlink()
            
    # 3. Lobotomize specific SDK headers that conflict with modern Linkage
    sdk_fixes = {
        "os_libc.h": [
            (r'extern\s+int\s+sprintf', '// Scrubbed sprintf'),
            (r'extern\s+int\s+strlen', '// Scrubbed strlen'),
            (r'extern\s+void\s+\*memcpy', '// Scrubbed memcpy')
        ],
        "os_convert.h": [
            (r'extern\s+u32\s+osVirtualToPhysical', '// Scrubbed v2p')
        ],
        "libaudio.h": [
            (r'typedef\s+ALDMAproc\s+\(\*ALDMANew\)\(void\s+\*\*state\);', 'typedef ALDMAproc (*ALDMANew)(void *state);')
        ]
    }

    for h_name, fixes in sdk_fixes.items():
        p = pr_folder / h_name
        if p.exists():
            content = p.read_text(errors='ignore')
            for pattern, replacement in fixes:
                content = re.sub(pattern, replacement, content)
            p.write_text(content)

    # 4. Global Source Patching
    clash_types = {"Gfx", "Acmd", "OSTask_t", "MtxF", "Mtx", "Vtx", "BoneTransform", "BoneTransformList", "VLA", "FLA", "OSLog", "OSRegion", "RamRomBuffer", "OSThread", "OSMesgQueue", "OSContPad", "OSThread_s"}

    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Ensure every file starts with our bridge
            if '#include "n64_types.h"' not in content:
                content = '#include "n64_types.h"\n' + content
                
            # Remove legacy boolean redefs
            content = content.replace("typedef int bool;", "/* Scrubbed bool */")
            
            # Fix sprintf linkages if they are manually declared
            content = content.replace("extern int sprintf", "// extern int sprintf")

            if content != original:
                path.write_text(content)
        except Exception: continue

    print("--- Surgical Linkage Fix Complete. Run Ninja! ---")

if __name__ == "__main__":
    deploy_dynamic_patch()
