import os
import re
from pathlib import Path

def project_mirroring():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v107.0] Mirroring Project Structures ---")

    # 1. SDK Eclipsing
    sdk_path = include_dir / "2.0L/PR"
    toxic = ["os.h", "gbi.h", "abi.h", "mbi.h", "gu.h", "sp.h", "ultratypes.h", "libaudio.h", "n_libaudio.h"]
    for header in toxic:
        p = sdk_path / header
        if p.exists():
            p.write_text("#include <n64_types.h>\n")

    # 2. Source Surgery
    for path in decomp.rglob("*.[ch]"):
        # CRITICAL: Do not modify n64_types.h itself or it loops
        if path.name == "n64_types.h": continue
        
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Map direct access back to our union layout
            content = content.replace("evt.midi", "evt.msg.midi")
            content = content.replace("evt.unk18", "evt.msg.unk18")
            
            # 64-bit Pointer alignment
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Wipe local clashing types
            content = content.replace("typedef int bool;", "// Removed")
            content = content.replace("typedef struct { float m[4][4]; } MtxF;", "// Removed")

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Mirroring Complete. ---")

if __name__ == "__main__":
    project_mirroring()
