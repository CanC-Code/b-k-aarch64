import os
import re
from pathlib import Path

def omni_harmonization():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v106.0] COMMENCING OMNI-HARMONIZATION ---")

    # 1. Total SDK Lockdown
    sdk_path = include_dir / "2.0L" / "PR"
    toxic = ["os.h", "gbi.h", "abi.h", "libaudio.h", "n_libaudio.h", "gu.h", "sp.h", "ultratypes.h"]
    for header in toxic:
        p = sdk_path / header
        if p.exists():
            # Replace legacy content with a pointer to our bridge
            p.write_text("#include <n64_types.h>\n")

    # 2. Source Surgery
    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Fix 64-bit pointer math truncation
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Fix ALEvent Member Access
            content = content.replace("evt.midi", "evt.msg.midi")
            content = content.replace("evt.unk18", "evt.msg.unk18")
            
            # Kill clashing local definitions
            content = content.replace("typedef int bool;", "// Removed")
            content = content.replace("typedef struct { float m[4][4]; } MtxF;", "// Removed")

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Harmonization v106.0 Complete. ---")

if __name__ == "__main__":
    omni_harmonization()
