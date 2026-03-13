import os
import re
from pathlib import Path

def structural_debridement():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v105.0] COMMENCING STRUCTURAL DEBRIDEMENT ---")

    # 1. Total SDK Lockout
    sdk_path = include_dir / "2.0L/PR"
    toxic = ["os.h", "gbi.h", "abi.h", "mbi.h", "gu.h", "sp.h", "ultratypes.h", "libaudio.h", "n_libaudio.h"]
    for header in toxic:
        p = sdk_path / header
        if p.exists():
            p.write_text("#include <n64_types.h>\n")

    # 2. Local Redefinition Cleanup
    # We search for manual 'typedef struct ... MtxF' or 'Vtx' and comment them out.
    clash_patterns = [
        r"typedef\s+struct\s*\{[^\}]+\}\s*MtxF\s*;",
        r"typedef\s+struct\s*\{[^\}]+\}\s*Mtx\s*;",
        r"typedef\s+struct\s*\{[^\}]+\}\s*Vtx\s*;",
        r"typedef\s+int\s+bool\s*;"
    ]

    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Force include of the bridge at the absolute top
            if "n64_types.h" not in content:
                content = "#include <n64_types.h>\n" + content

            # Comment out colliding local types
            for pattern in clash_patterns:
                content = re.sub(pattern, "/* Collision Removed */", content, flags=re.MULTILINE)

            # Fix specific ALEvent access patterns (midi -> msg.midi)
            content = content.replace("evt.midi", "evt.msg.midi")
            content = content.replace("evt.unk18", "evt.msg.unk18")
            content = content.replace("evt.ticks", "evt.ticks")

            # Fix 64-bit pointer truncation
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Debridement Complete. Triggering Build. ---")

if __name__ == "__main__":
    structural_debridement()
