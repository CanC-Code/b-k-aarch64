#!/usr/bin/env python3
import re
import os
from pathlib import Path

def nuclear_harmonization():
    cwd = Path.cwd().resolve()
    decomp_root = cwd / "decomp-files"
    include_dir = decomp_root / "include"
    sdk_dir = include_dir / "2.0L" / "PR"
    
    print(f"--- [v85.5] NUCLEAR AUDIO HARMONIZATION ---")

    # 1. Neutralize bool.h immediately
    bool_h = include_dir / "bool.h"
    bool_h.write_text("#ifndef _BOOL_H_\n#define _BOOL_H_\n#include <stdbool.h>\n#endif\n")

    # 2. Blackhole all hardware-centric SDK headers
    toxic = ["ultratypes.h", "abi.h", "mbi.h", "gbi.h", "os_libc.h", "os_thread.h", "os_message.h", "os_cont.h", "os.h", "gu.h"]
    for name in toxic:
        target = sdk_dir / name
        if target.exists():
            target.write_text("#include <n64_types.h>\n")

    # 3. Precision repair for Audio Codec source
    for path in decomp_root.rglob("*.[ch]"):
        if "PR/" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Fix: Remove local bool typedefs
            content = content.replace("typedef int bool;", "/* SH-REMOVED */")
            
            # Fix: (Acmd) member access logic. 
            # Modern Clang doesn't like MIPS-style union-to-struct member access
            content = re.sub(r'->\s*(A_LOADBUFF|A_ADPCM|A_LOOP)', r' | \1', content)
            
            # Fix: 64-bit Pointer Truncation
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Fix: string.h styling
            content = content.replace('"string.h"', '<string.h>')

            if content != original:
                path.write_text(content)
        except: pass

    print(f"--- Harmonization Complete. ---")

if __name__ == "__main__":
    nuclear_harmonization()
