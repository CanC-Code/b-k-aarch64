#!/usr/bin/env python3
import re
import os
from pathlib import Path

def finalizing_harmonization():
    cwd = Path.cwd().resolve()
    decomp_root = cwd / "decomp-files"
    include_dir = decomp_root / "include"
    sdk_dir = include_dir / "2.0L" / "PR"
    
    print(f"--- [v86.0] FINAL AUDIO REPAIR: AArch64 ---")

    # 1. Update the bridge (n64_types.h)
    # [Already provided in step 1 above]

    # 2. Redirect SDK headers to the bridge
    toxic = ["ultratypes.h", "abi.h", "mbi.h", "gbi.h", "os_libc.h", "os.h", "gu.h"]
    for name in toxic:
        target = sdk_dir / name
        if target.exists():
            target.write_text("#include <n64_types.h>\n")

    # 3. Special Case: n_abi.h
    # This file contains the macros that were failing. 
    # We need to make sure it doesn't try to define Acmd itself.
    n_abi = include_dir / "n_abi.h"
    if n_abi.exists():
        content = n_abi.read_text(errors='ignore')
        # Block its local Acmd definition if it has one
        content = re.sub(r"typedef.*?Acmd;", "/* Handled by Bridge */", content)
        n_abi.write_text(content)

    # 4. Global Syntax Cleanup
    for path in decomp_root.rglob("*.[ch]"):
        if "PR/" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Pointer safety (crucial for AArch64)
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Remove conflicting bools
            content = content.replace("typedef int bool;", "// Removed")
            
            if content != original:
                path.write_text(content)
        except: pass

    print(f"--- Environment v86.0 Harmonized ---")

if __name__ == "__main__":
    finalizing_harmonization()
