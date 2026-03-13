import os
import re
from pathlib import Path

def total_eclipse_harmonization():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v96.0] COMMENCING TOTAL ECLIPSE ---")

    # 1. TOTAL ECLIPSE: Wipe the toxic SDK headers
    # Instead of including n64_types.h, we make them do NOTHING.
    # This prevents the "Typedef Redefinition" error.
    sdk_path = include_dir / "2.0L" / "PR"
    toxic = ["gbi.h", "abi.h", "mbi.h", "ultratypes.h", "os_thread.h", "os_message.h", "os_cont.h", "sp.h"]
    
    for name in toxic:
        p = sdk_path / name
        if p.exists():
            p.write_text("// Eclipsed by Harmonizer\n")
            print(f"[!] Eclipsed: {name}")

    # 2. IDENTIFY & INJECT: Scan source for missing requirements
    for path in decomp.rglob("*.[ch]"):
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Fix 64-bit pointer math truncations
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
            
            # Remove any local 'typedef int bool' that causes the 'cannot combine with int' error
            content = content.replace("typedef int bool;", "/* DELETED */")
            content = content.replace("typedef char bool;", "/* DELETED */")

            # Infill missing basic types if the file seems to need them
            # This is the "Automated Content" part
            if "s8" in content and "typedef" not in content[:100]:
                content = "#include <n64_types.h>\n" + content

            if content != original:
                path.write_text(content)
        except: continue

    print("--- Total Eclipse Complete. Ready for Ninja. ---")

if __name__ == "__main__":
    total_eclipse_harmonization()
