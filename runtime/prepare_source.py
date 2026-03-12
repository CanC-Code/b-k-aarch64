#!/usr/bin/env python3
import re
from pathlib import Path

def setup_headers(decomp_root: Path):
    # 1. Create a bulletproof n64_types.h
    types_h = decomp_root / "include" / "n64_types.h"
    types_h.write_text("""#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

typedef uint8_t u8;   typedef int8_t s8;
typedef uint16_t u16; typedef int16_t s16;
typedef uint32_t u32; typedef int32_t s32;
typedef uint64_t u64; typedef int64_t s64;
typedef float f32;    typedef double f64;

#ifndef TRUE
  #define TRUE true
  #define FALSE false
#endif

// Opaque types for the engine
typedef struct { uint32_t w0; uint32_t w1; } Awords;
typedef struct { uint32_t w0; uint32_t w1; } Apolef;
typedef uint64_t Gfx;
typedef uint64_t Acmd;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { u8 d[16]; } ALHeap;
typedef struct { u8 d[64]; } Aadpcm;
typedef struct { u8 d[128]; } ADPCM_STATE;

#ifndef bcopy
#define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

#endif
""", encoding='utf-8')

    # 2. Force Replace "Toxic" SDK Headers with simple redirects
    # This prevents the compiler from ever seeing 'long Mtx_t' again.
    toxic_headers = [
        "2.0L/PR/ultratypes.h",
        "2.0L/PR/abi.h",
        "2.0L/PR/mbi.h",
        "2.0L/PR/gbi.h",
        "2.0L/PR/os_libc.h"
    ]
    for h_name in toxic_headers:
        h_path = decomp_root / "include" / h_name
        if h_path.exists():
            h_path.write_text("#include <n64_types.h>\n", encoding='utf-8')

    # 3. Clean libaudio.h (Remove problematic typedefs entirely)
    libaudio = decomp_root / "include/2.0L/PR/libaudio.h"
    if libaudio.exists():
        content = libaudio.read_text(encoding='utf-8', errors='ignore')
        # Remove struct definitions that we've already defined in n64_types.h
        patterns = [
            r"typedef struct \{.*?\} ALHeap;",
            r"typedef struct \{.*?\} Aadpcm;",
            r"typedef short ADPCM_STATE\[.*?\];"
        ]
        for p in patterns:
            content = re.sub(p, f"/* SH-REMOVED-TYPE */", content, flags=re.DOTALL)
        libaudio.write_text(content, encoding='utf-8')

def apply_source_fixes(content):
    # Standard Include Pathing
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "core1/mem.h"', '#include <string.h>')
    # 64-bit Pointer alignment fix
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    return content

def main():
    repo_root = Path("./")
    decomp_root = repo_root / "decomp-files"
    print("[>] SourceHarmonizer v83.0: Stub & Redirect Mode")
    
    setup_headers(decomp_root)
    
    for root in [decomp_root / "src", decomp_root / "include"]:
        for file_path in root.rglob("*.[ch]"):
            if file_path.suffix == ".h" and "PR/" in str(file_path): continue
            raw = file_path.read_text(encoding='utf-8', errors='ignore')
            # Remove any previous SH preambles
            content = re.sub(r'/\* SH-.* \*/\n', '', raw)
            fixed = apply_source_fixes(content)
            file_path.write_text(f"/* SH-AUTOMORPH-V83.0 */\n{fixed}", encoding='utf-8')

if __name__ == "__main__": main()
