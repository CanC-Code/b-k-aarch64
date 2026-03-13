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

// 2. Hardware Structs (Only the absolute bare minimum 64-bit hardware patches)
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
typedef ALDMAproc (*ALDMANew)(void **state);

typedef u32 OSIntMask;

// 3. System Standard Libraries
#include <string.h>
#include <stdlib.h>
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
    
    print("--- [v163.0] RUNNING DYNAMIC INJECTION SCRUBBER ---")
    
    # 1. Write the slimmed down bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. Unblock standard C libraries, but keep them empty so we use Android's
    for sh in ["string.h", "math.h", "stdarg.h", "time.h", "basic_types.h"]:
        p = include_dir / sh
        if p.exists(): p.unlink()
            
    sched_p = pr_folder / "sched.h"
    if sched_p.exists():
        sched_p.unlink()

    # 3. Dynamic Source Code Patching
    # Instead of defining the structs, we fix the specific 64-bit bugs in the original source
    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Unconditionally inject the bridge
            if '#include "n64_types.h"' not in content:
                content = '#include "n64_types.h"\n' + content
                
            # Scrub standard library collisions
            if path.name in ["mem.h", "functions.h", "synthInternals.h"]:
                content = re.sub(r'void\s+memcpy\s*\([^;]+;', '/* Scrubbed memcpy */;', content)
                content = re.sub(r'void\s+memmove\s*\([^;]+;', '/* Scrubbed memmove */;', content)
                content = re.sub(r'void\s*\*\s*malloc\s*\([^;]+;', '/* Scrubbed malloc */;', content)
                content = re.sub(r'void\s*\*\s*realloc\s*\([^;]+;', '/* Scrubbed realloc */;', content)
                
            # --- THE DYNAMIC FIXES ---
            # 1. Fix ALLowPass redefinition collision directly in synthInternals.h
            if path.name == "synthInternals.h":
                 content = re.sub(r'typedef\s+struct\s*ALLowPass_s\s*\{[^}]*\}\s*ALLowPass\s*;', '/* Scrubbed ALLowPass_s */', content)

            # 2. Fix the ALDelay rsdelta array index bug directly in synthInternals.h
            if "rsdelta" in content and "ALDelay" in content:
                content = content.replace("f32 rsdelta;", "s32 rsdelta; // 64-bit int fix")

            # 3. Fix standard struct sizes colliding with 64-bit pointers
            # The only hardware structs we MUST block are the ones we define in n64_types.h
            hardware_types = ["MtxF", "Mtx", "Vtx", "BoneTransform", "BoneTransformList", "VLA", "FLA", "OSLog", "OSErrorHandler", "OSRegion", "RamRomBuffer", "OSThread", "OSMesgQueue", "OSContPad"]
            for ct in hardware_types:
                content = re.sub(r'typedef\s+struct\s*(?:[a-zA-Z0-9_]+\s*)?\{[^{}]*\}\s*' + ct + r'\s*;', f'/* Terminated {ct} */', content)
                content = re.sub(r'typedef\s+union\s*(?:[a-zA-Z0-9_]+\s*)?\{[^{}]*\}\s*' + ct + r'\s*;', f'/* Terminated {ct} */', content)
                content = re.sub(r'typedef\s+(struct|union)\s+[a-zA-Z0-9_]+\s+' + ct + r'\s*;', f'/* Scrubbed fwd {ct} */', content)

            if content != original:
                path.write_text(content)
        except Exception:
            continue

    # 4. Patch Android Wrappers
    android_cpp_dir = root / "Android" / "app" / "src" / "main" / "cpp"
    for path in android_cpp_dir.rglob("*.cpp"):
        try:
            content = path.read_text(errors='ignore')
            original = content
            content = content.replace('#include "tools/rare_decompression.h"', '#include "rare_decompression.h"')
            for ct in hardware_types:
                 content = re.sub(r'typedef\s+struct\s*(?:[a-zA-Z0-9_]+\s*)?\{[^{}]*\}\s*' + ct + r'\s*;', f'/* Scrubbed {ct} */', content)
            if content != original:
                path.write_text(content)
        except Exception:
            pass

    print("--- Dynamic Scrubber Complete. Run Ninja! ---")

if __name__ == "__main__":
    deploy_dynamic_patch()
