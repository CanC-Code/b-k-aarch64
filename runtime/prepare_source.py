#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-AUTOMORPH-ACTIVE-V82.4-FINAL */"

def deep_clean_sdk(decomp_root: Path):
    """SDK Sanitation: Finalizing hardware and library abstraction."""
    # 1. Neutralize bool.h
    bool_h = decomp_root / "include" / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#include <stdbool.h>\n", encoding='utf-8')

    # 2. DELETE CLASHING HEADERS
    death_list = ["string.h", "time.h", "math.h", "assert.h", "core1/mem.h"]
    for name in death_list:
        p = decomp_root / "include" / name
        if p.exists(): p.unlink()

    # 3. PATCH os_libc.h (The source of bcopy/memmove conflicts)
    os_libc = decomp_root / "include/2.0L/PR/os_libc.h"
    if os_libc.exists():
        content = os_libc.read_text(encoding='utf-8', errors='ignore')
        # We rename the SDK's bcopy declaration to something that won't clash
        content = content.replace("extern void     bcopy", "extern void n64_sdk_bcopy_unused")
        os_libc.write_text(content, encoding='utf-8')

    # 4. MASTER TYPES (Primitives Only)
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
typedef volatile uint32_t vu32;
#ifndef TRUE
  #define TRUE true
  #define FALSE false
#endif
#ifndef _ALHEAP_H_
  #define _ALHEAP_H_
  typedef struct { u8 dummy[16]; } ALHeap;
#endif
#endif
""", encoding='utf-8')

    # 5. MASTER BRIDGE (Function Prototypes)
    bridge_h = decomp_root / "include" / "n64_bridge.h"
    bridge_h.write_text("""#ifndef _N64_BRIDGE_H_
#define _N64_BRIDGE_H_
#include <n64_types.h>
#include <string.h>

// Safe bcopy redirect using compiler built-in
#undef bcopy
#define bcopy(src, dst, n) __builtin_memmove(dst, src, n)

// Audio Manager Prototypes
struct AudioInfo_s;
typedef struct AudioInfo_s AudioInfo;
bool audioManager_handleFrameMsg(AudioInfo *info, AudioInfo *prev_info);

#endif
""", encoding='utf-8')

def apply_source_fixes(content, file_path):
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "core1/mem.h"', '#include <string.h>')
    # 64-bit Pointer Truncation Repair
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\\1', content)
    return content

def process_file(path):
    if path.suffix == ".cpp": return False
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    content = re.sub(r'/\\* SH-.*\\*/.*?#endif\\n', '', raw_content, flags=re.DOTALL)
    fixed_content = apply_source_fixes(content, path)
    # Inject minimal local preamble
    final_output = f"{PREAMBLE_MARKER}\\n#include <n64_bridge.h>\\n" + fixed_content
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path("./")
    print("[>] SourceHarmonizer v82.4: Bridging Prototypes")
    deep_clean_sdk(repo_root / "decomp-files")
    for root in [repo_root / "decomp-files/src", repo_root / "decomp-files/include"]:
        for file_path in root.rglob("*.[ch]"):
            process_file(file_path)

if __name__ == "__main__": main()
