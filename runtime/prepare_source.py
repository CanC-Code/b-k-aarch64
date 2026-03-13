import os
import re
from pathlib import Path

def dynamic_requirement_injection():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v98.0] Starting Advanced Autoinfill & Loop-Proofing ---")

    # 1. Total SDK Lockdown (Eclipsing)
    sdk_path = include_dir / "2.0L" / "PR"
    toxic = ["os.h", "gbi.h", "abi.h", "libaudio.h", "n_libaudio.h", "ultratypes.h", "sp.h"]
    for header in toxic:
        p = sdk_path / header
        if p.exists():
            p.write_text("// Total Eclipse: See n64_types.h for definitions.\n")

    # 2. Requirement Scan & Infill
    # This dictionary maps specific words to the bridge inclusion
    REQUIREMENTS = ["s8", "u8", "s32", "u32", "Gfx", "ALPan", "ALHeap", "ALLink"]

    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Fix 64-bit pointer truncation (Critical for Android NDK)
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Remove legacy bool conflict
            content = content.replace("typedef int bool;", "/* ALIGNED */")

            # Check if file needs the bridge and doesn't have it
            needs_bridge = any(req in content for req in REQUIREMENTS)
            if needs_bridge and "n64_types.h" not in content:
                content = "#include <n64_types.h>\n" + content

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Harmonization Complete. ---")

if __name__ == "__main__":
    dynamic_requirement_injection()
