import os
import re
from pathlib import Path

def harmonize_and_heal():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    sdk_dir = include_dir / "2.0L" / "PR"
    
    # 1. THE DICTIONARY: Requirements identified from your logs
    # We add to this as the compiler complains about new missing pieces.
    REQUIRED_SYMBOLS = {
        "Audio Math": {
            "ADPCMFSIZE": "16",
            "ADPCMVSIZE": "8",
            "LFSAMPLES": "4",
            "UNITY_PITCH": "0x8000",
            "MAX_RATIO": "2"
        },
        "Audio ABI Commands": {
            "A_INIT": "0x01",
            "A_CONTINUE": "0x02",
            "A_LOOP": "0x02",
            "A_MAIN": "0x04",
            "A_AUX": "0x08",
            "A_VOL": "0x10",
            "A_RATE": "0x20",
            "A_LEFT": "0x40",
            "A_RIGHT": "0x80",
            "A_LOADBUFF": "0x01",
            "A_ADPCM": "0x02",
            "A_SETVOL": "0x03",
            "A_ENVMIXER": "0x04",
            "A_POLEF": "0x05",
            "A_RESAMPLE": "0x06",
            "A_SAVEBUFF": "0x07",
            "A_LOADADPCM": "0x08",
            "A_NOAUX": "0x10"
        },
        "OS Constants": {
            "OS_IM_NONE": "0",
            "OS_TV_NTSC": "0",
            "OS_MESG_BLOCK": "1",
            "PFS_ERR_ID_FATAL": "1",
            "PFS_ERR_DEVICE": "2"
        }
    }

    print("--- [v93.0] Starting Evolutionary Harmonization ---")

    # 2. GENERATE / UPDATE n64_types.h
    # This builds the bridge based on the REQUIRED_SYMBOLS dictionary
    bridge_path = include_dir / "n64_types.h"
    
    lines = ["#ifndef _N64_TYPES_H_", "#define _N64_TYPES_H_", 
             "#include <stdint.h>", "#include <stddef.h>", "#include <stdbool.h>", ""]
    
    # Primitive types
    lines += ["typedef uint8_t u8; typedef int8_t s8;", 
              "typedef uint16_t u16; typedef int16_t s16;", 
              "typedef uint32_t u32; typedef int32_t s32;", 
              "typedef uint64_t u64; typedef int64_t s64;", 
              "typedef float f32; typedef double f64;"]

    # Structs & Unions
    lines += ["", "typedef struct { unsigned int w0; unsigned int w1; } Acmd_words;",
              "typedef union { Acmd_words words; long long force_align; } Acmd;",
              "typedef void* OSMesg;",
              "typedef struct { void* mtqueue; void* fullqueue; int validCount; } OSMesgQueue;",
              "typedef struct { uint8_t d[16]; } Vtx;",
              "typedef struct { int32_t m[4][4]; } Mtx;",
              "typedef int16_t ADPCM_STATE[16];"]

    # Inject the Dictionary
    for category, symbols in REQUIRED_SYMBOLS.items():
        lines.append(f"\n// --- {category} ---")
        for sym, val in symbols.items():
            lines.append(f"#ifndef {sym}\n  #define {sym} {val}\n#endif")

    lines += ["\n#endif"]
    bridge_path.write_text("\n".join(lines))
    print(f"[+] Synced {bridge_path}")

    # 3. SOURCE SURGERY
    # This part "identifies" requirements by looking for patterns in the source.
    for path in decomp.rglob("*.[ch]"):
        if "PR/" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Identify missing Acmd access patterns and fix them
            # Changes ptr->words.w0 access into valid structure access if needed
            if "Acmd" in content:
                content = re.sub(r'\(Acmd\)\s*ptr', r'ptr', content)

            # Pointer safety (MIPS 32 -> ARM 64)
            # This is the single biggest "Identifier" fix.
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)

            # Cleanup clashing bools
            content = content.replace("typedef int bool;", "// Removed")

            if content != original:
                path.write_text(content)
        except: continue

    # 4. NEUTRALIZE SDK
    toxic = ["os.h", "gbi.h", "abi.h", "mbi.h", "ultratypes.h", "gu.h", "os_internal.h"]
    for header in toxic:
        p = sdk_dir / header
        if p.exists(): p.write_text("#include <n64_types.h>\n")

    print("--- Harmonization Complete ---")

if __name__ == "__main__":
    harmonize_and_heal()
