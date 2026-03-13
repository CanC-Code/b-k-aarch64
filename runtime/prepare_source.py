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

def scrub_types_ast(content, type_names):
    pattern = re.compile(r'typedef\s+(struct|union)\s*([a-zA-Z0-9_]+\s*)?\{')
    pos = 0
    while True:
        match = pattern.search(content, pos)
        if not match: break
        start_idx = match.start()
        brace_count = 0
        in_struct = False
        end_brace_idx = -1
        for i in range(match.end() - 1, len(content)):
            if content[i] == '{':
                brace_count += 1
                in_struct = True
            elif content[i] == '}':
                brace_count -= 1
                if in_struct and brace_count == 0:
                    end_brace_idx = i
                    break
        if end_brace_idx != -1:
            after_brace = content[end_brace_idx+1 : end_brace_idx+150]
            m = re.match(r'\s*([^;]+);', after_brace)
            if m:
                decl = m.group(1)
                tokens = [t.strip().lstrip('*') for t in decl.split(',')]
                if any(t in type_names for t in tokens):
                    full_match_end = end_brace_idx + 1 + m.end()
                    content = content[:start_idx] + "/* Scrubbed block by AST parser */\n" + content[full_match_end:]
                    pos = start_idx
                    continue
        pos = match.end()
    for name in type_names:
        content = re.sub(r'typedef\s+(struct|union)\s+[a-zA-Z0-9_]+\s+' + name + r'\s*;', f'/* Scrubbed fwd {name} */\n', content)
    return content

def deploy_dynamic_patch():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    pr_folder = include_dir / "2.0L" / "PR"
    
    print("--- [v165.0] RUNNING DYNAMIC BOOLEAN SCRUBBER ---")
    
    (include_dir / "n64_types.h").write_text(BASE_BRIDGE_CONTENT)

    for sh in ["string.h", "math.h", "stdarg.h", "time.h", "basic_types.h"]:
        p = include_dir / sh
        if p.exists(): p.unlink()
            
    # CRITICAL: If bool.h exists, kill the redefinition
    bool_h = include_dir / "bool.h"
    if bool_h.exists():
        print(f"Found {bool_h.name}, scrubbing legacy typedefs...")
        content = bool_h.read_text(errors='ignore')
        content = content.replace("typedef int bool;", "/* Handled by stdbool.h */")
        content = content.replace("typedef int32_t bool;", "/* Handled by stdbool.h */")
        bool_h.write_text(content)

    sched_p = pr_folder / "sched.h"
    if sched_p.exists():
        sched_p.unlink()

    clash_types = {"Gfx", "Acmd", "OSTask_t", "MtxF", "Mtx", "Vtx", "BoneTransform", "BoneTransformList", "VLA", "FLA", "OSLog", "OSRegion", "RamRomBuffer", "OSThread", "OSMesgQueue", "OSContPad"}

    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            if '#include "n64_types.h"' not in content:
                content = '#include "n64_types.h"\n' + content
                
            # Inline boolean scrubber for headers/sources
            content = content.replace("typedef int bool;", "/* Scrubbed bool */")
                
            if path.name in ["mem.h", "functions.h", "synthInternals.h"]:
                content = re.sub(r'void\s+memcpy\s*\([^;]+;', '/* Scrubbed memcpy */;', content)
                content = re.sub(r'void\s+memmove\s*\([^;]+;', '/* Scrubbed memmove */;', content)
                content = re.sub(r'void\s*\*\s*malloc\s*\([^;]+;', '/* Scrubbed malloc */;', content)
                content = re.sub(r'void\s*\*\s*realloc\s*\([^;]+;', '/* Scrubbed realloc */;', content)
                
            if path.name == "synthInternals.h":
                 content = re.sub(r'typedef\s+struct\s*ALLowPass_s\s*\{[^}]*\}\s*ALLowPass\s*;', '/* Scrubbed ALLowPass_s */', content)

            if "rsdelta" in content and "ALDelay" in content:
                content = content.replace("f32 rsdelta;", "s32 rsdelta; // 64-bit int fix")

            content = scrub_types_ast(content, clash_types)
            content = re.sub(r'typedef\s+.*?\(\*ALDMANew\).*?;', '/* Scrubbed ALDMANew */', content)
            content = re.sub(r'typedef\s+.*?\(\*OSErrorHandler\).*?;', '/* Scrubbed OSErrorHandler */', content)

            if content != original:
                path.write_text(content)
        except Exception:
            continue

    print("--- Boolean Scrubber Complete. Run Ninja! ---")

if __name__ == "__main__":
    deploy_dynamic_patch()
