import os
import re
from pathlib import Path

# THE ATOMIC BRIDGE: No dependencies, just raw types.
BASE_BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>

// 1. ATOMIC DEFINITIONS (Must be first for recursive includes)
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar; typedef volatile uint32_t vu32;

typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { int16_t ob[3]; uint16_t flag; int16_t tc[2]; uint8_t cn[4]; } Vtx_t;
typedef union { Vtx_t v; long long force_align; } Vtx;

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

// 2. SYSTEM SHIMS
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>

// 3. BLOCKADE LEGACY SDK
#define _ULTRATYPES_H_
#define __OS_H__
#define _OS_H_
#define _ULTRA64_H_
#define _GBI_H_

typedef uint32_t OSId;
typedef uint32_t OSPri;
typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;
typedef void* ALHeap;

#endif // _N64_TYPES_H_
"""

def deploy_nuclear_foundation():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v179.0] DEPLOYING NUCLEAR FOUNDATION ---")
    
    # 1. Update the Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 2. SURGERY: Strip all includes from string.h, structs.h, and model.h
    # We want these to be PURE data structures that rely ONLY on the bridge.
    targets = ["string.h", "structs.h", "model.h"]
    for t in targets:
        p = include_dir / t
        if p.exists():
            content = p.read_text(errors='ignore')
            # Remove any line that includes a project header or N64 header
            # This breaks the circular dependency chain.
            content = re.sub(r'#include\s*["<](structs|model|string|ultra64|os|PR/).*?[">]', '/* Dependency Purged */', content)
            
            # Clean up clashing typedefs in structs.h
            if t == "structs.h":
                content = re.sub(r'typedef struct\s*\{.*?\}\s*MtxF\s*;', '/* Atomic MtxF */', content, flags=re.DOTALL)
                content = content.replace('ALHeap', 'void*')
            
            p.write_text(content)

    # 3. Suppress the PR folder once and for all
    pr_path = include_dir / "2.0L" / "PR"
    if pr_path.exists():
        for h in pr_path.glob("*.h"):
            h.write_text("#include \"n64_types.h\"\n")

if __name__ == "__main__":
    deploy_nuclear_foundation()
