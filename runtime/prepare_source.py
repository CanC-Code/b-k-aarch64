import os
import re
from pathlib import Path

def master_autoinfill():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v100.0] COMMENCING MASTER AUTOINFILL ---")

    # 1. SDK Eclipsing
    sdk_path = include_dir / "2.0L" / "PR"
    toxic = ["os.h", "gbi.h", "abi.h", "libaudio.h", "n_libaudio.h", "gu.h", "sp.h", "ultratypes.h"]
    for header in toxic:
        p = sdk_path / header
        if p.exists():
            p.write_text("#include <n64_types.h>\n")

    # 2. Source Vaccination
    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Force n64_types inclusion at the top
            if "n64_types.h" not in content:
                content = "#include <n64_types.h>\n" + content

            # Fix specific ALEvent access pattern: evt.msg.midi -> evt.midi
            # The engine uses a flattened structure in some versions.
            content = content.replace("evt.midi", "evt.msg.midi")
            content = content.replace("evt.unk18", "evt.msg.unk18")

            # Fix 64-bit pointer math (The uintptr_t vaccination)
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Kill local bool redefinitions
            content = content.replace("typedef int bool;", "/* ALIGNED */")

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Engine v100.0 Ready for Deployment ---")

if __name__ == "__main__":
    master_autoinfill()
