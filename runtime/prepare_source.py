import os
import re
from pathlib import Path

def structural_vaccination():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v101.0] Commencing Deep Structural Vaccination ---")

    # 1. Neutralize SDK Headers
    sdk_path = include_dir / "2.0L" / "PR"
    toxic = ["os.h", "gbi.h", "abi.h", "libaudio.h", "n_libaudio.h", "gu.h", "sp.h", "ultratypes.h"]
    for header in toxic:
        p = sdk_path / header
        if p.exists():
            p.write_text("#include <n64_types.h>\n")

    # 2. Source Surgery
    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Fix specific ALEvent access patterns (midi -> msg.midi)
            # This handles files like code_21AF0.c automatically
            content = content.replace("evt.midi", "evt.msg.midi")
            content = content.replace("evt.unk18", "evt.msg.unk18")
            content = content.replace("evt.ticks", "evt.ticks")

            # Fix 64-bit pointer truncation (Crucial for Android)
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Ensure bridge inclusion
            if "n64_types.h" not in content:
                content = "#include <n64_types.h>\n" + content

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Vaccination Complete. Ready for Ninja. ---")

if __name__ == "__main__":
    structural_vaccination()
