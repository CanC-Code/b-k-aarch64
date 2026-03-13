import os
import re
from pathlib import Path

def atomic_debridement():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v108.0] COMMENCING ATOMIC DEBRIDEMENT ---")

    # 1. Neutralize SDK Headers physically
    sdk_path = include_dir / "2.0L/PR"
    toxic = ["os.h", "gbi.h", "abi.h", "mbi.h", "gu.h", "sp.h", "ultratypes.h", "libaudio.h", "n_libaudio.h"]
    for header in toxic:
        p = sdk_path / header
        if p.exists():
            p.write_text("#include <n64_types.h>\n")

    # 2. Source-Level Redefinition Removal
    # This prevents the "typedef redefinition" error by commenting out local versions.
    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Force include bridge at the top
            if "n64_types.h" not in content:
                content = "#include <n64_types.h>\n" + content

            # Nuke the specific structs.h redefinitions causing the current errors
            content = re.sub(r'typedef\s+struct\s*\{[^}]*\}\s*MtxF\s*;', '/* CLASH REMOVED */', content)
            content = re.sub(r'typedef\s+struct\s*\{[^}]*\}\s*Mtx\s*;', '/* CLASH REMOVED */', content)
            content = content.replace("typedef int bool;", "/* CLASH REMOVED */")

            # Map Rare-specific ALEvent calls to our bridge union
            content = content.replace("evt.midi", "evt.msg.midi")
            content = content.replace("evt.unk18", "evt.msg.unk18")
            
            # Pointer safety
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Debridement Complete. Triggering Build. ---")

if __name__ == "__main__":
    atomic_debridement()
