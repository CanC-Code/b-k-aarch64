#!/usr/bin/env python3
import re
import os
from pathlib import Path

def master_harmonization():
    cwd = Path.cwd().resolve()
    decomp_root = cwd / "decomp-files"
    include_dir = decomp_root / "include"
    sdk_dir = include_dir / "2.0L" / "PR"
    
    print(f"--- [v86.5] MASTER SYMBOL RESTORATION ---")

    # 1. Neutralize low-level SDK headers
    toxic = ["ultratypes.h", "abi.h", "mbi.h", "gbi.h", "os_libc.h", "os.h", "gu.h"]
    for name in toxic:
        target = sdk_dir / name
        if target.exists():
            target.write_text("#include <n64_types.h>\n")

    # 2. Precision repair for 'n_abi.h'
    # This file often contains conflicting Acmd or primitive definitions.
    n_abi = include_dir / "n_abi.h"
    if n_abi.exists():
        content = n_abi.read_text(errors='ignore')
        # Block the local Acmd definition so our bridge takes over
        content = re.sub(r"typedef.*?Acmd;", "/* Restored by Bridge */", content)
        # Block local SHIFTL/SHIFTR if they exist
        content = content.replace("#define _SHIFTL", "//#define _SHIFTL")
        n_abi.write_text(content)

    # 3. Global Source Syntax Pass
    for path in decomp_root.rglob("*.[ch]"):
        if "PR/" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # Pointer safety for AArch64
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Remove any local typedefs that clash with stdbool.h
            content = content.replace("typedef int bool;", "// Removed")
            
            if content != original:
                path.write_text(content)
        except: pass

    print(f"--- Harmonization Complete. Ready for Build ---")

if __name__ == "__main__":
    master_harmonization()
