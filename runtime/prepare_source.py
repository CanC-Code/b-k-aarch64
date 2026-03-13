import os
import re
from pathlib import Path

def absolute_sanitization():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    
    print("--- [v109.0] COMMENCING ABSOLUTE SANITIZATION ---")

    # 1. SDK Physical Deletion (The only way to be sure)
    sdk_path = decomp / "include/2.0L/PR"
    headers = ["os.h", "gbi.h", "abi.h", "mbi.h", "gu.h", "sp.h", "ultratypes.h", "libaudio.h", "n_libaudio.h"]
    for h in headers:
        p = sdk_path / h
        if p.exists():
            # Replace file content with just our bridge to stop redefinitions
            p.write_text("#include <n64_types.h>\n")

    # 2. Deep File Sanitization
    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Force Include Bridge at line 1
            if "n64_types.h" not in content:
                content = "#include <n64_types.h>\n" + content

            # Nuke Clashing Block Definitions (MtxF, Mtx, Vtx)
            # This regex finds 'typedef struct { ... } Name;' and removes it
            content = re.sub(r'typedef\s+struct\s*\{[^}]*\}\s*(MtxF|Mtx|Vtx|ALEvent)\s*;', '/* Overridden by Bridge */', content)
            
            # Map Rare's audio calls (evt.ticks, evt.midi)
            content = content.replace("evt.midi", "evt.msg.midi")
            content = content.replace("evt.unk18", "evt.msg.unk18")
            
            # 64-bit Pointer alignment fix
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Sanitization v109.0 Complete. ---")

if __name__ == "__main__":
    absolute_sanitization()
