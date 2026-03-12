#!/usr/bin/env python3
import re
import os
from pathlib import Path

def sweep_and_harmonize():
    cwd = Path.cwd().resolve()
    decomp_root = cwd / "decomp-files"
    include_dir = decomp_root / "include"
    sdk_dir = include_dir / "2.0L" / "PR"
    
    print(f"--- [v89.0] REQUIREMENT SWEEPER: AArch64 ---")

    # 1. SDK Redirection (Absolute)
    toxic = ["ultratypes.h", "abi.h", "mbi.h", "gbi.h", "os_libc.h", "os.h", "gu.h", "os_internal.h"]
    for name in toxic:
        target = sdk_dir / name
        if target.exists():
            target.write_text("#include <n64_types.h>\n")

    # 2. Source Surgery
    for path in decomp_root.rglob("*.[ch]"):
        if "PR/" in str(path): continue
        try:
            content = path.read_text(errors='ignore')
            original = content
            
            # 2a. Fix implicit declaration conflicts (e.g. audioManager_handleFrameMsg)
            # If the file defines it but the call came before the definition, Clang errors.
            # We inject a forward declaration to be safe.
            if "audioManager_handleFrameMsg" in content and "bool audioManager_handleFrameMsg" not in content[:500]:
                content = "struct AudioInfo; bool audioManager_handleFrameMsg(void *info, void *prev);\n" + content

            # 2b. Global Pointer safety
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # 2c. Force OS_IM_NONE
            if "OS_IM_NONE" in content and "#define OS_IM_NONE" not in content:
                content = "#ifndef OS_IM_NONE\n#define OS_IM_NONE 0\n#endif\n" + content

            if content != original:
                path.write_text(content)
        except: pass

    print(f"--- Harmonization Complete. ---")

if __name__ == "__main__":
    sweep_and_harmonize()
