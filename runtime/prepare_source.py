import os
import re
from pathlib import Path

def master_alignment():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v102.0] COMMENCING DEEP STRUCTURAL ALIGNMENT ---")

    # 1. Neutralize Legacy Headers
    # We strip their contents to stop them from overriding our types.
    sdk_path = include_dir / "2.0L" / "PR"
    toxic = ["os.h", "gbi.h", "abi.h", "mbi.h", "gu.h", "sp.h", "ultratypes.h"]
    for header in toxic:
        p = sdk_path / header
        if p.exists():
            p.write_text("#include <n64_types.h>\n")

    # 2. Kill the bool conflict physically
    # bool.h is often the source of "cannot combine with previous int"
    bool_h = include_dir / "bool.h"
    if bool_h.exists():
        bool_h.write_text("// Eclipsed by Harmonizer\n")

    # 3. Source Vaccination
    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Fix 64-bit pointer truncation (Critical for ARM64 stability)
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Remove legacy bool redefinitions
            content = content.replace("typedef int bool;", "/* ALIGNED */")
            content = content.replace("typedef char bool;", "/* ALIGNED */")

            # Force bridge inclusion
            if "n64_types.h" not in content:
                content = "#include <n64_types.h>\n" + content

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Alignment Complete. Ready for Ninja Build. ---")

if __name__ == "__main__":
    master_alignment()
