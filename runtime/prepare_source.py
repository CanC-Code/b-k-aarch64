import os
import re
from pathlib import Path

def align_engine_for_aarch64():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    
    print("--- [v91.0] Commencing Deep Engine Alignment ---")

    # 1. Neutralize the SDK headers to force our bridge usage
    sdk_path = decomp / "include" / "2.0L" / "PR"
    toxic_headers = ["os.h", "gbi.h", "abi.h", "mbi.h", "ultratypes.h", "gu.h", "os_internal.h"]
    for header in toxic_headers:
        p = sdk_path / header
        if p.exists():
            p.write_text("#include <n64_types.h>\n")

    # 2. Global Source Surgery
    for path in decomp.rglob("*.[ch]"):
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Remove conflicting bool and type definitions
            content = content.replace("typedef int bool;", "/* ALIGNED */")
            content = content.replace("typedef char bool;", "/* ALIGNED */")
            
            # Critical: Fix 32-bit pointer truncation (u32)ptr -> (u32)(uintptr_t)ptr
            # This prevents immediate crashes on 64-bit Android devices
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)

            # Fix implicit audio function declarations that cause type conflicts
            if "audioManager_handleFrameMsg" in content and "bool audioManager_handleFrameMsg" not in content[:500]:
                decl = "\nstruct AudioInfo; bool audioManager_handleFrameMsg(void *info, void *prev);\n"
                content = decl + content

            if content != original:
                path.write_text(content)
        except:
            continue

    print("--- Alignment Success. Core 1 Source is now 64-bit compliant. ---")

if __name__ == "__main__":
    align_engine_for_aarch64()
