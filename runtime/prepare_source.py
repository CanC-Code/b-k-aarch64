#!/usr/bin/env python3
import re
import os
from pathlib import Path

def setup_harmonized_environment():
    cwd = Path.cwd().resolve()
    decomp_root = cwd / "decomp-files"
    include_dir = decomp_root / "include"
    sdk_dir = include_dir / "2.0L" / "PR"
    
    print(f"--- [v87.0] NUCLEAR SDK REDIRECT: AArch64 ---")

    # 1. Update the Master Bridge (Created/Modified in Step 1)

    # 2. Complete Neutralization of SDK Hardware Headers
    # We add os_internal.h and os_internal_exception.h to the list
    toxic = [
        "ultratypes.h", "abi.h", "mbi.h", "gbi.h", "os_libc.h", 
        "os_thread.h", "os_message.h", "os_cont.h", "os.h", "gu.h",
        "os_internal.h", "os_internal_exception.h"
    ]
    for name in toxic:
        target = sdk_dir / name
        if target.exists():
            target.write_text("#include <n64_types.h>\n")
            print(f"[!] Neutralized: {name}")

    # 3. GLOBAL SOURCE REPAIR
    for path in decomp_root.rglob("*.[ch]"):
        if "PR/" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Pointer safety for AArch64
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            # Remove local bool typedefs
            content = content.replace("typedef int bool;", "// Removed")
            
            if content != original:
                path.write_text(content)
        except: pass

    print(f"--- Harmonization v87.0 Complete ---")

if __name__ == "__main__":
    setup_harmonized_environment()
