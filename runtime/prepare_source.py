import os
import re
from pathlib import Path

def rare_aware_harmonization():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = root / "decomp-files/include"
    
    print("--- [v104.0] COMMENCING RARE-AWARE HARMONIZATION ---")

    # 1. Neutralize SDK Headers
    sdk_path = include_dir / "2.0L/PR"
    toxic = ["os.h", "gbi.h", "abi.h", "mbi.h", "gu.h", "sp.h", "ultratypes.h", "libaudio.h", "n_libaudio.h"]
    for header in toxic:
        p = sdk_path / header
        if p.exists():
            p.write_text("#include <n64_types.h>\n")

    # 2. Project-wide code injection
    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Fix 64-bit pointer truncation (The uintptr_t vaccine)
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Fix ALEvent Member Access: Map 'evt.midi' to our union 'evt.msg.midi'
            # The log showed code trying to access evt.midi direktly.
            content = content.replace("evt.midi", "evt.msg.midi")
            content = content.replace("evt.unk18", "evt.msg.unk18")
            
            # Physically remove the old bool.h content to prevent redefinition errors
            if path.name == "bool.h":
                content = "// Eclipsed"

            # Force include n64_types.h
            if "n64_types.h" not in content:
                content = "#include <n64_types.h>\n" + content

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Harmonization Complete. ---")

if __name__ == "__main__":
    rare_aware_harmonization()
