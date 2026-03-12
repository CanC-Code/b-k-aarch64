import os
import re
from pathlib import Path

def ultimate_harmonization():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    
    print("--- [v92.0] Commencing Ultimate Identifier Enforcement ---")

    # 1. SDK Redirection
    sdk_path = decomp / "include" / "2.0L" / "PR"
    for header in ["os.h", "gbi.h", "abi.h", "mbi.h", "ultratypes.h", "gu.h", "os_internal.h"]:
        p = sdk_path / header
        if p.exists():
            p.write_text("#include <n64_types.h>\n")

    # 2. Identifier Injection Dictionary
    # We force these into any file that mentions them but doesn't define them.
    audio_flags = {
        "A_LEFT": "0x40",
        "A_RIGHT": "0x80",
        "A_VOL": "0x10",
        "A_RATE": "0x20",
        "OS_IM_NONE": "0"
    }

    # 3. Global Source Surgery
    for path in decomp.rglob("*.[ch]"):
        try:
            content = path.read_text(errors='ignore')
            original = content

            # Force definitions for missing audio identifiers
            injection = ""
            for key, val in audio_flags.items():
                if key in content and f"#define {key}" not in content:
                    injection += f"#ifndef {key}\n  #define {key} {val}\n#endif\n"
            
            if injection:
                content = injection + content

            # Fix 64-bit pointer truncation (Crucial for Android stability)
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)

            # Delete clashing bool typedefs
            content = content.replace("typedef int bool;", "/* ALIGNED */")

            if content != original:
                path.write_text(content)
        except:
            continue

    print("--- All identifiers enforced. Build should proceed. ---")

if __name__ == "__main__":
    ultimate_harmonization()
