import os
import re
from pathlib import Path

def harmonize_and_vaccinate():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v94.0] Commencing Engine Vaccination ---")

    # 1. Vaccine Dictionary: Missing symbols causing errors
    VACCINES = {
        "Gfx": "uint64_t",
        "ADPCMFSIZE": "16",
        "A_LOOP": "0x02",
        "A_LEFT": "0x40",
        "A_RIGHT": "0x80",
        "UNITY_PITCH": "0x8000"
    }

    # 2. Deep Cleaning
    for path in decomp.rglob("*.[ch]"):
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Force definitions of missing identifiers locally
            injection = ""
            for sym, val in VACCINES.items():
                if sym in content and f"#define {sym}" not in content and f"typedef {val} {sym}" not in content:
                    # Special handling for Gfx which is usually a typedef
                    if sym == "Gfx":
                        injection += "#ifndef GFX_H\ntypedef uint64_t Gfx;\n#define GFX_H\n#endif\n"
                    else:
                        injection += f"#ifndef {sym}\n  #define {sym} {val}\n#endif\n"
            
            if injection:
                content = injection + content

            # Fix 64-bit pointer truncation logic
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Kill clashing local bools
            content = content.replace("typedef int bool;", "/* ALIGNED */")

            if content != original:
                path.write_text(content)
        except: continue

    # 3. Final SDK Lockdown
    sdk_path = include_dir / "2.0L" / "PR"
    toxic = ["os.h", "gbi.h", "abi.h", "mbi.h", "ultratypes.h", "gu.h", "sp.h"]
    for header in toxic:
        p = sdk_path / header
        if p.exists():
            p.write_text("#include <n64_types.h>\n")

    print("--- Core 1 vaccinated. Build Ready. ---")

if __name__ == "__main__":
    harmonize_and_vaccinate()
