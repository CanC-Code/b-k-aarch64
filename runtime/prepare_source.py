import os
import re
from pathlib import Path

# Bridge with defensive definitions
BASE_BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <time.h>
#include <sched.h>

// 1. Primitive Types (Shielded)
#ifndef _ULTRATYPES_H_
#define _ULTRATYPES_H_
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;
#endif

// 2. Fundamental Structs (Defining as the "Source of Truth")
#ifndef _N64_STRUCTS_DEFINED_
#define _N64_STRUCTS_DEFINED_
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { int16_t ob[3]; uint16_t flag; int16_t tc[2]; uint8_t cn[4]; } Vtx_t;
typedef union { Vtx_t v; long long force_align; } Vtx;
#endif

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

typedef void* ALHeap;
typedef void* OSTask;
typedef uint32_t OSId;
typedef uint32_t OSPri;
typedef uint64_t OSTime;
typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;

#if defined(__cplusplus)
extern "C" {
#endif
    static inline int sched_yield_compat(void) { return sched_yield(); }
#if defined(__cplusplus)
}
#endif

#endif // _N64_TYPES_H_
"""

def deploy_surgical_patch():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v177.0] DEPLOYING SURGICAL COLLISION FIX ---")
    
    # 1. Update Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. SURGERY: Remove conflicting types from structs.h
    structs_h = include_dir / "structs.h"
    if structs_h.exists():
        content = structs_h.read_text(errors='ignore')
        # Remove the Mtx/MtxF definitions that clash with n64_types.h
        content = re.sub(r'typedef struct\s*\{.*?\}\s*MtxF\s*;', '/* MtxF in n64_types.h */', content, flags=re.DOTALL)
        content = re.sub(r'typedef struct\s*\{.*?\}\s*Mtx\s*;', '/* Mtx in n64_types.h */', content, flags=re.DOTALL)
        # Fix the ALHeap error
        content = content.replace('ALHeap', 'void* /* ALHeap */')
        structs_h.write_text(content)

    # 3. FIX: rare_decompression.h path collision
    rare_decomp_cpp = root / "Android/app/src/main/cpp/tools/rare_decompression.cpp"
    if rare_decomp_cpp.exists():
        text = rare_decomp_cpp.read_text()
        text = text.replace('#include "tools/rare_decompression.h"', '#include "rare_decompression.h"')
        rare_decomp_cpp.write_text(text)

    # 4. FIX: NativeBridge.cpp Namespace/Inclusion issues
    bridge_cpp = root / "Android/app/src/main/cpp/ultra/NativeBridge.cpp"
    if bridge_cpp.exists():
        text = bridge_cpp.read_text()
        # Ensure system headers are physically at the very top for C++
        if '#include <string.h>' not in text:
            text = "#include <string.h>\n#include <stdlib.h>\n#include <stdio.h>\n" + text
        bridge_cpp.write_text(text)

if __name__ == "__main__":
    deploy_surgical_patch()
