#!/usr/bin/env python3
import re
import os
from pathlib import Path

def setup_harmonized_environment():
    cwd = Path.cwd().resolve()
    decomp_root = cwd / "decomp-files"
    # Target the specific JNI folder for the Android project
    cpp_dir = cwd / "Android" / "app" / "src" / "main" / "cpp"
    
    print(f"[>] Harmonizing Environment at: {decomp_root}")
    
    # 1. Generate the Bridge Header
    include_dir = decomp_root / "include"
    include_dir.mkdir(parents=True, exist_ok=True)
    bridge_h = include_dir / "n64_types.h"
    bridge_h.write_text("""#ifndef _N64_TYPES_H_
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

#define _ULTRA64_H_
#define _GU_H_
#define _ALHEAP_H_

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
typedef struct { u8 d[16]; } ALHeap;
typedef struct { u8 d[64]; } Aadpcm;
typedef struct { u8 d[128]; } ADPCM_STATE;

#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif
#endif
""")

    # 2. Generate NativeBridge.cpp (Ensures CMake always has a target)
    cpp_dir.mkdir(parents=True, exist_ok=True)
    bridge_cpp = cpp_dir / "NativeBridge.cpp"
    bridge_cpp.write_text("""#include <jni.h>
#include <android/log.h>
#include <n64_types.h>

extern "C" JNIEXPORT jstring JNICALL
Java_com_bk_aarch64_NativeBridge_stringFromJNI(JNIEnv* env, jobject thiz) {
    return env->NewStringUTF("Banjo-Kazooie Engine Harmonized - v84.2");
}
""")

    # 3. Neutralize SDK Headers
    sdk_dir = include_dir / "2.0L" / "PR"
    toxic = ["ultratypes.h", "abi.h", "mbi.h", "gbi.h", "os_libc.h", "gu.h"]
    for name in toxic:
        target = sdk_dir / name
        if target.exists():
            target.write_text("#include <n64_types.h>\\n")

    # 4. Global Source Cleanup
    for path in decomp_root.rglob("*.[ch]"):
        if "PR/" in str(path): continue
        content = path.read_text(errors='ignore')
        content = content.replace('"string.h"', '<string.h>')
        content = re.sub(r'\(u32\)\s*(&?\\w+(?:->|\\.)?\\w*)', r'(u32)(uintptr_t)\\1', content)
        path.write_text(content)

if __name__ == "__main__":
    setup_harmonized_environment()
