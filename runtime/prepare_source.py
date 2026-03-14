import os
import re
from pathlib import Path

# THE STANDALONE BRIDGE: Zero project dependencies.
BASE_BRIDGE_CONTENT = r"""
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>

/** 1. N64 PRIMITIVES **/
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

/** 2. PROJECT MACROS **/
#define PAIR(type, name) type name[2]
#define TUPLE(type, name) type name[3]
#define TUPLE_PAIR(type, name) type name[2][3]
#define FREE_LIST(type) struct { struct type *head; int32_t count; }

// Forward declarations for common engine structs
struct struct12s; struct struct_68_s; struct BKModelBin; struct BKVertexList;

/** 3. C++ COMPATIBILITY **/
#ifdef __cplusplus
  #include <cstring>
  #include <cstdlib>
  #include <cstdio>
  extern "C" {
#else
  #include <string.h>
  #include <stdlib.h>
  #include <stdio.h>
#endif

typedef void* OSMesg;
typedef struct { void* mt; void* full; int32_t count; } OSMesgQueue;
typedef struct OSThread_s { struct OSThread_s *next; int32_t priority; uint8_t d[256]; } OSThread;
typedef uint32_t OSId;
typedef uint32_t OSPri;
typedef uint64_t OSTime;
typedef void* ALHeap;
typedef void* OSTask;

#ifdef __cplusplus
}
#endif

#define _ULTRATYPES_H_
#define _ULTRA64_H_
#define _GBI_H_
#define _BOOL_H_ 

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#endif // _N64_TYPES_H_
"""

def deploy_scorched_earth():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v184.0] DEPLOYING SCORCHED EARTH PATCH ---")
    
    # 1. Physically RENAME project headers that clash with C/C++ standards
    clash_map = {
        "string.h": "n64_string_legacy.h",
        "bool.h": "n64_bool_legacy.h"
    }
    
    for old_name, new_name in clash_map.items():
        old_p = include_dir / old_name
        new_p = include_dir / new_name
        if old_p.exists():
            print(f"Renaming {old_name} -> {new_name} to prevent system shadowing.")
            old_p.rename(new_p)

    # 2. Update the Bridge
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    # 3. PURGE internal includes from project headers
    # We want model.h and structs.h to be "dumb" data definitions
    for target in ["structs.h", "model.h"]:
        p = include_dir / target
        if p.exists():
            text = p.read_text(errors='ignore')
            # Remove all internal project includes
            text = re.sub(r'#include\s*["<](string|structs|model|bool|ultra64|os|PR/).*?[">]', '/* Purged */', text)
            # Prepend the bridge
            text = '#include "n64_types.h"\n' + text
            p.write_text(text)

    # 4. FIX path for rare_decompression.cpp
    rare_cpp = root / "Android/app/src/main/cpp/tools/rare_decompression.cpp"
    if rare_cpp.exists():
        text = rare_cpp.read_text()
        text = text.replace('#include "tools/rare_decompression.h"', '#include "rare_decompression.h"')
        rare_cpp.write_text(text)

    # 5. NativeBridge namespace safety
    bridge_cpp = root / "Android/app/src/main/cpp/ultra/NativeBridge.cpp"
    if bridge_cpp.exists():
        text = bridge_cpp.read_text()
        if 'using namespace std;' not in text:
            text = "#include <string.h>\nusing namespace std;\n" + text
        bridge_cpp.write_text(text)

if __name__ == "__main__":
    deploy_scorched_earth()
