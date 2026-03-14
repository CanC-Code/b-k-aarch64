import os
import re
from pathlib import Path

def deploy_system_dominance():
    root = Path.cwd().resolve()
    include_dir = root / "decomp-files" / "include"
    
    print("--- [v180.0] DEPLOYING SYSTEM DOMINANCE PATCH ---")

    # 1. Neutralize conflicting project headers
    # string.h is the primary offender causing NDK <cstring> to fail
    conflicting_headers = ["string.h", "bool.h"]
    for header in conflicting_headers:
        p = include_dir / header
        if p.exists():
            print(f"Neutralizing {header}...")
            # We don't delete it (it might be needed for internal refs), 
            # but we empty it and make it redirect to the system version.
            if header == "string.h":
                p.write_text("#include_next <string.h>\n#include_next <strings.h>\n")
            elif header == "bool.h":
                p.write_text("#include <stdbool.h>\n")

    # 2. Fix the rare_decompression path
    # The compiler complained: 'tools/rare_decompression.h' file not found
    rare_cpp = root / "Android/app/src/main/cpp/tools/rare_decompression.cpp"
    if rare_cpp.exists():
        content = rare_cpp.read_text()
        content = content.replace('#include "tools/rare_decompression.h"', '#include "rare_decompression.h"')
        rare_cpp.write_text(content)

    # 3. Inject Namespace Fixes into Bridge files
    # NativeBridge.cpp needs to know that memset is a standard C function
    bridge_cpp = root / "Android/app/src/main/cpp/ultra/NativeBridge.cpp"
    if bridge_cpp.exists():
        content = bridge_cpp.read_text()
        # Ensure we use standard includes for C++ compatibility
        if "#include <string.h>" not in content:
            content = "#include <string.h>\n#include <stdio.h>\n#include <stdlib.h>\n" + content
        bridge_cpp.write_text(content)

    # 4. Final sweep of the N64 Bridge (n64_types.h)
    bridge_h = include_dir / "n64_types.h"
    if bridge_h.exists():
        text = bridge_h.read_text()
        # Add the ALHeap and OSTask definitions we missed
        if "typedef void* ALHeap;" not in text:
            text = text.replace("#endif // _N64_TYPES_H_", "typedef void* ALHeap;\ntypedef void* OSTask;\n#endif // _N64_TYPES_H_")
        bridge_h.write_text(text)

if __name__ == "__main__":
    deploy_system_dominance()
