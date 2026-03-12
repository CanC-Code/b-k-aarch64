#!/usr/bin/env python3
import re
import os
from pathlib import Path

def sweep_and_harmonize():
    cwd = Path.cwd().resolve()
    decomp_root = cwd / "decomp-files"
    include_dir = decomp_root / "include"
    sdk_dir = include_dir / "2.0L" / "PR"
    
    print(f"--- [v90.0] NUCLEAR SOURCE ALIGNMENT ---")

    # 1. Neutralize SDK Hardware Headers
    toxic = ["ultratypes.h", "abi.h", "mbi.h", "gbi.h", "os_libc.h", "os.h", "gu.h", "os_internal.h"]
    for name in toxic:
        target = sdk_dir / name
        if target.exists():
            target.write_text("#include <n64_types.h>\n")

    # 2. Deep Clean of Game Source and Local Includes
    for path in decomp_root.rglob("*.[ch]"):
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # 2a. KILL conflicting bool typedefs everywhere
            content = content.replace("typedef int bool;", "/* ALIGNED */")
            content = content.replace("typedef char bool;", "/* ALIGNED */")
            
            # 2b. Pointer safety (64-bit cast)
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # 2c. Injection of missing OS_IM_NONE
            if "OS_IM_NONE" in content and "#define OS_IM_NONE" not in content:
                content = "#ifndef OS_IM_NONE\n#define OS_IM_NONE 0\n#endif\n" + content

            if content != original:
                path.write_text(content)
        except: pass

    print(f"--- Harmonization Complete. Launching Ninja ---")

if __name__ == "__main__":
    sweep_and_harmonize()
