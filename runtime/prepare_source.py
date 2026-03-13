import os
import re
from pathlib import Path

def terminator_sanitization():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v110.0] COMMENCING TERMINATOR SANITIZATION ---")

    # 1. Terminate Legacy Headers
    toxic = [
        "2.0L/PR/os.h", "2.0L/PR/gbi.h", "2.0L/PR/abi.h", "2.0L/PR/mbi.h", 
        "2.0L/PR/gu.h", "2.0L/PR/sp.h", "2.0L/PR/ultratypes.h", 
        "2.0L/PR/libaudio.h", "2.0L/PR/n_libaudio.h", "bool.h"
    ]
    for h in toxic:
        p = include_dir / h
        if p.exists():
            # Physically emptying the file prevents all redefinitions
            p.write_text("/* Terminated by Script */\n")
            print(f"[!] Terminated: {h}")

    # 2. Deep File Sweeping
    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Nuke Clashing Block Definitions (MtxF, Mtx, Vtx)
            content = re.sub(r'typedef\s+struct\s*\{[^}]*\}\s*(MtxF|Mtx|Vtx|ALEvent)\s*;', '/* Terminated */', content)
            
            # Nuke inline bool redefinitions
            content = content.replace("typedef int bool;", "/* Terminated */")
            content = content.replace("typedef char bool;", "/* Terminated */")

            # Map Rare's custom audio calls to the standard layout
            content = content.replace("evt.midi", "evt.msg.midi")
            content = content.replace("evt.unk18", "evt.msg.unk18")
            
            # 64-bit Pointer alignment fix for Android
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Sanitization v110.0 Complete. ---")

if __name__ == "__main__":
    terminator_sanitization()
