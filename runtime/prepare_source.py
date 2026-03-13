import os
import re
from pathlib import Path

def logic_gated_harmonization():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v97.0] COMMENCING LOOP-PROOF HARMONIZATION ---")

    # 1. Total Eclipse: Neutralize legacy SDK headers
    # We replace them with a simple comment to prevent redefinitions.
    sdk_path = include_dir / "2.0L" / "PR"
    toxic = [
        "gbi.h", "abi.h", "mbi.h", "ultratypes.h", "os_thread.h", 
        "os_message.h", "os_cont.h", "sp.h", "os.h", "libaudio.h"
    ]
    
    for name in toxic:
        p = sdk_path / name
        if p.exists():
            p.write_text("// Eclipsed to prevent redefinition conflicts.\n")

    # 2. Source Surgery and Identifier Injection
    # We identify files that need n64_types.h but don't have it.
    for path in decomp.rglob("*.[ch]"):
        # SKIP the bridge itself to prevent infinite nesting
        if path.name == "n64_types.h":
            continue
            
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Remove conflicting bool and type definitions
            content = content.replace("typedef int bool;", "/* DELETED */")
            content = content.replace("typedef char bool;", "/* DELETED */")
            
            # Fix 64-bit pointer truncation (MIPS 32-bit addresses -> ARM64)
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)

            # Check if file uses N64 types but doesn't include the bridge
            # If so, we prepended it (only if not already there)
            if ("u8" in content or "s32" in content or "Gfx" in content) and "n64_types.h" not in content:
                content = "#include <n64_types.h>\n" + content

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Harmonization v97.0 Complete. ---")

if __name__ == "__main__":
    logic_gated_harmonization()
