import os
import re
from pathlib import Path

def evolutionary_harmonizer():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    
    # THE MASTER REPOSITORY OF N64 KNOWLEDGE
    # This dictionary automatically populates files that are "missing" info.
    KNOWLEDGE_BASE = {
        "A_INIT": "0x01", "A_CONTINUE": "0x02", "A_MAIN": "0x04", "A_AUX": "0x08",
        "A_VOL": "0x10", "A_RATE": "0x20", "A_LEFT": "0x40", "A_RIGHT": "0x80",
        "A_LOADBUFF": "0x01", "A_ADPCM": "0x02", "A_SETVOL": "0x03", 
        "A_ENVMIXER": "0x04", "A_POLEF": "0x05", "A_RESAMPLE": "0x06",
        "A_SAVEBUFF": "0x07", "A_LOADADPCM": "0x08", "A_NOAUX": "0x10",
        "ADPCMFSIZE": "16", "ADPCMVSIZE": "8", "LFSAMPLES": "4",
        "UNITY_PITCH": "0x8000", "OS_IM_NONE": "0", "OS_MESG_BLOCK": "1"
    }

    print("--- [v95.0] Commencing Automated Content Injection ---")

    # 1. First, repair the actual bridge to ensure it's robust
    bridge = decomp / "include" / "n64_types.h"
    bridge_content = """#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stdbool.h>

typedef uint8_t u8; typedef int16_t s16; typedef uint16_t u16; 
typedef int32_t s32; typedef uint32_t u32; typedef uint64_t u64;
typedef float f32;

// Audio States
typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int16_t POLEF_STATE[4];
typedef int16_t ENVMIX_STATE[40];

// Structs
typedef struct { unsigned int w0; unsigned int w1; } Acmd_words;
typedef union { Acmd_words words; long long force_align; } Acmd;
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[16]; } Vtx;

#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

#endif
"""
    bridge.write_text(bridge_content)

    # 2. THE SCANNER: Identify and Insert requirements
    for path in decomp.rglob("*.[ch]"):
        if "PR/" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Find every key in our Knowledge Base that is used but not defined in the file
            missing_defs = []
            for key, val in KNOWLEDGE_BASE.items():
                if key in content and f"#define {key}" not in content:
                    missing_defs.append(f"#ifndef {key}\n  #define {key} {val}\n#endif")
            
            if missing_defs:
                # Inject right after the first include or at the very top
                content = "\n".join(missing_defs) + "\n" + content

            # Pointer safety (MIPS 32 -> ARM 64)
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Remove clashing bools
            content = content.replace("typedef int bool;", "// Removed")

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Harmonization v95.0 Complete. Triggering Build. ---")

if __name__ == "__main__":
    evolutionary_harmonizer()
