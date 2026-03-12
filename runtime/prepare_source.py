#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-AUTOMORPH-ACTIVE-V82.8-STABLE */"

def deep_clean_sdk(decomp_root: Path):
    """
    Surgically neutralizes ONLY the specific clashing types.
    """
    # 1. Kill the bool.h recursion loop
    bool_h = decomp_root / "include" / "bool.h"
    bool_h.write_text("#pragma once\n#include <stdbool.h>\n", encoding='utf-8')

    # 2. Establish n64_types.h (The Proxy Bridge)
    types_h = decomp_root / "include" / "n64_types.h"
    types_h.write_text(f"""#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

typedef uint8_t u8;   typedef int8_t s8;
typedef uint16_t u16; typedef int16_t s16;
typedef uint32_t u32; typedef int32_t s32;
typedef uint64_t u64; typedef int64_t s64;
typedef float f32;    typedef double f64;
typedef volatile uint32_t vu32; typedef volatile int32_t vs32;

#ifndef TRUE
  #define TRUE true
  #define FALSE false
#endif

typedef struct {{ uint32_t w0; uint32_t w1; }} Awords;

// Use real structs for proxies, not void
typedef struct {{ u8 d[16]; }} _SH_ALHeap;
typedef struct {{ u8 d[64]; }} _SH_Aadpcm;
typedef struct {{ u8 d[64]; }} _SH_ADPCM_STATE;

#define ALHeap _SH_ALHeap
#define Aadpcm _SH_Aadpcm
#define ADPCM_STATE _SH_ADPCM_STATE

#ifndef bcopy
#define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

bool audioManager_handleFrameMsg(void *info, void *prev_info);

#endif
""", encoding='utf-8')

    # 3. Precision SDK Neutralization
    target_headers = {
        "2.0L/PR/libaudio.h": ["} ALHeap;", "} Aadpcm;"],
        "2.0L/PR/abi.h": ["} Aadpcm;", "typedef short ADPCM_STATE"],
        "2.0L/PR/os_libc.h": ["extern void     bcopy"]
    }

    for h_name, targets in target_headers.items():
        h_path = decomp_root / "include" / h_name
        if h_path.exists():
            lines = h_path.read_text(encoding='utf-8', errors='ignore').splitlines()
            new_lines = []
            skip_until = None
            
            for line in lines:
                # If we are in a skip block (searching for the end of the struct)
                if skip_until and skip_until in line:
                    new_lines.append(f"// [SH-END] {line}")
                    skip_until = None
                    continue
                if skip_until:
                    new_lines.append(f"// [SH-HIDDEN] {line}")
                    continue

                # Check if this line starts a block we want to hide
                if any(t in line for t in targets):
                    # If it's a one-liner like bcopy
                    if "extern" in line or "typedef short" in line:
                        new_lines.append(f"// [SH-NEUTRALIZED] {line}")
                    else:
                        # If it's a struct end, we need to find its start (backwards)
                        # Actually simpler: just neutralize the line if it's the target
                        new_lines.append(f"// [SH-TARGET] {line}")
                else:
                    new_lines.append(line)
            
            h_path.write_text("\n".join(new_lines), encoding='utf-8')

    # 4. Final ultratypes.h check
    u_types = decomp_root / "include/2.0L/PR/ultratypes.h"
    if u_types.exists():
        u_types.write_text("#include <n64_types.h>\n", encoding='utf-8')

def process_file(path):
    if path.suffix == ".cpp": return False
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    content = re.sub(r'/\* SH-.* \*/.*', '', raw_content, flags=re.DOTALL)
    
    # Header redirects to system
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "core1/mem.h"', '#include <string.h>')
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    
    final_output = f"{PREAMBLE_MARKER}\n" + content
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path("./")
    decomp_root = repo_root / "decomp-files"
    print("[>] SourceHarmonizer v82.8: Surgical Neutralization Active")
    deep_clean_sdk(decomp_root)
    for root in [decomp_root / "src", decomp_root / "include"]:
        for file_path in root.rglob("*.[ch]"):
            process_file(file_path)

if __name__ == "__main__": main()
