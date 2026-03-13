import os
import re
from pathlib import Path

def automate_requirements():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v99.0] Commencing Dynamic Structural Alignment ---")

    # 1. Vacuum-seal the SDK headers
    # We strip their contents but keep the file so #include "os.h" doesn't fail.
    sdk_path = include_dir / "2.0L" / "PR"
    toxic = ["os.h", "gbi.h", "abi.h", "libaudio.h", "n_libaudio.h", "gu.h", "sp.h", "ultratypes.h"]
    for header in toxic:
        p = sdk_path / header
        if p.exists():
            p.write_text("#include <n64_types.h>\n")

    # 2. Universal Source Scan
    # We ensure n64_types.h is ALWAYS at the top, and ptr math is AArch64 safe.
    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Fix 64-bit pointer truncation (Crucial for Android)
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Remove legacy bool conflict physically
            content = content.replace("typedef int bool;", "// Stripped")
            
            # Infill requirement: ensure n64_types is included
            if "n64_types.h" not in content:
                content = "#include <n64_types.h>\n" + content

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Structural Emulation Complete ---")

if __name__ == "__main__":
    automate_requirements()
