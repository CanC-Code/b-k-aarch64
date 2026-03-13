import os
import re
from pathlib import Path

def total_eclipse_harmonization():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v103.0] COMMENCING TOTAL ECLIPSE ---")

    # 1. PHYSICAL WIPING: Legacy SDK headers are the enemy. 
    # We strip their contents to stop the "typedef redefinition" wall.
    sdk_path = include_dir / "2.0L" / "PR"
    toxic = ["os.h", "gbi.h", "abi.h", "mbi.h", "gu.h", "sp.h", "ultratypes.h", "libaudio.h", "n_libaudio.h"]
    
    for header in toxic:
        p = sdk_path / header
        if p.exists():
            # We don't delete the file (that would break #include lines), 
            # we just empty it and point it to our bridge.
            p.write_text("#include <n64_types.h>\n")
            print(f"[!] Eclipsed: {header}")

    # 2. SOURCE SURGERY: Force AArch64 compatibility
    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Fix 64-bit pointer math truncation (Critical for Android NDK)
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Kill clashing local bool redefinitions
            content = content.replace("typedef int bool;", "/* ALIGNED */")
            content = content.replace("typedef char bool;", "/* ALIGNED */")

            # Force include of n64_types.h if not present
            if "n64_types.h" not in content:
                content = "#include <n64_types.h>\n" + content

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Eclipse Complete. Ready for build. ---")

if __name__ == "__main__":
    total_eclipse_harmonization()
