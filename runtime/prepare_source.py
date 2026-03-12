#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-AUTOMORPH-ACTIVE-V82.4-FINAL */"

def deep_clean_sdk(decomp_root: Path):
    """SDK Sanitation: Removing the foundation-level conflicts."""
    # 1. Neutralize bool.h
    bool_h = decomp_root / "include" / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#include <stdbool.h>\n", encoding='utf-8')

    # 2. DELETE CLASHING HEADERS
    death_list = [
        decomp_root / "include/string.h",
        decomp_root / "include/time.h",
        decomp_root / "include/math.h",
        decomp_root / "include/assert.h",
        decomp_root / "include/core1/mem.h"
    ]
    for path in death_list:
        if path.exists(): path.unlink()

    # 3. Patch os_libc.h (Aggressive removal of clashing declarations)
    os_libc = decomp_root / "include/2.0L/PR/os_libc.h"
    if os_libc.exists():
        lines = os_libc.read_text(encoding='utf-8', errors='ignore').splitlines()
        new_lines = []
        for line in lines:
            # Physically remove the declaration so macros can't 'attack' it
            if "bcopy" in line or "strlen" in line or "memcpy" in line:
                new_lines.append(f"// [SH-REMOVED] {line}")
            else:
                new_lines.append(line)
        os_libc.write_text("\n".join(new_lines), encoding='utf-8')

    # 4. HARDEN n64_types.h
    types_h = decomp_root / "include" / "n64_types.h"
    types_h.write_text("""#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stddef.h>

// Harden bool for C99/C11
#if !defined(__cplusplus) && !defined(__bool_true_false_are_defined)
  typedef _Bool bool;
  #define true 1
  #define false 0
  #define __bool_true_false_are_defined 1
#endif

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

#ifndef _ALHEAP_H_
#define _ALHEAP_H_
typedef struct { u8 dummy[16]; } ALHeap;
#endif

// Prototypes for internal game functions
struct AudioInfo_s; 
typedef struct AudioInfo_s AudioInfo;
bool audioManager_handleFrameMsg(struct AudioInfo_s *info, struct AudioInfo_s *prev_info);

#endif
""", encoding='utf-8')

def apply_source_fixes(content):
    # Standard Include Renaming
    content = content.replace('#include "string.h"', '#include <string.h>')
    content = content.replace('#include "core1/mem.h"', '#include <string.h>')
    
    # 64-bit Pointer Truncation Repair
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\\1', content)
    
    # Inject the bcopy redirect AFTER includes to prevent header pollution
    redirect = "\\n#ifndef bcopy\\n#define bcopy(src, dst, n) __builtin_memmove(dst, src, n)\\n#endif\\n"
    
    # Find the last include and put the redirect after it
    includes = list(re.finditer(r'#include.*\\n', content))
    if includes:
        last_pos = includes[-1].end()
        content = content[:last_pos] + redirect + content[last_pos:]
    else:
        content = redirect + content
        
    return content

def process_file(path):
    if path.suffix == ".cpp": return False
    raw_content = path.read_text(encoding='utf-8', errors='ignore')
    
    # Strip old markers and apply new logic
    content = re.sub(r'/\\* SH-.*\\*/.*?#endif\\n', '', raw_content, flags=re.DOTALL)
    fixed_content = apply_source_fixes(content)
    
    final_output = f"{PREAMBLE_MARKER}\\n" + fixed_content
    
    if final_output != raw_content:
        path.write_text(final_output, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path("./")
    decomp_root = repo_root / "decomp-files"
    print("[>] SourceHarmonizer v82.4: Solving Semantic Redefinition")
    deep_clean_sdk(decomp_root)
    
    for root in [decomp_root / "src", decomp_root / "include"]:
        for file_path in root.rglob("*.[ch]"):
            process_file(file_path)

if __name__ == "__main__": main()
