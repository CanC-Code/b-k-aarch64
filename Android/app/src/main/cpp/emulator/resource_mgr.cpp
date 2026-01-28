import os
import shutil
import re
from pathlib import Path

def patch_android_compatibility(cpp_dir):
    print("--- Applying Android Compatibility Patches ---")

    # 1. Rename Shadowing Headers
    shadow_headers = ["string.h", "stdio.h", "ctype.h", "stdlib.h", "time.h"]
    renamed_map = {}

    include_path = cpp_dir / "include"
    for header in shadow_headers:
        original = include_path / header
        if original.exists():
            new_name = f"game_{header}"
            target = include_path / new_name
            os.rename(original, target)
            renamed_map[header] = new_name
            print(f"Renamed shadow header: {header} -> {new_name}")

    # 2. Global Search and Replace for Renamed Headers
    if renamed_map:
        print("Updating include references...")
        for root, _, files in os.walk(cpp_dir):
            for file in files:
                if file.endswith((".c", ".h", ".cpp", ".hpp")):
                    fpath = Path(root) / file
                    try:
                        content = fpath.read_text(errors='ignore')
                        changed = False
                        for old, new in renamed_map.items():
                            if f'#include "{old}"' in content:
                                content = content.replace(f'#include "{old}"', f'#include "{new}"')
                                changed = True
                        if changed:
                            fpath.write_text(content)
                    except Exception as e:
                        print(f"Could not patch {file}: {e}")

    # 3. Fix 'bool' redeclaration
    bool_h = include_path / "bool.h"
    if bool_h.exists():
        content = bool_h.read_text()
        if "ifndef __cplusplus" not in content:
            patched = content.replace("typedef int bool;", "#ifndef __cplusplus\ntypedef int bool;\n#endif")
            bool_h.write_text(patched)
            print("Patched: bool.h")

    # 4. Inject standard headers + sched.h (for sched_yield)
    wrapper_files = [
        cpp_dir / "ultra" / "NativeBridge.cpp",
        cpp_dir / "emulator" / "stubs.cpp",
        cpp_dir / "emulator" / "resource_mgr.cpp"
    ]
    for file_path in wrapper_files:
        if file_path.exists():
            content = file_path.read_text()
            injection = (
                "#include <stddef.h>\n"
                "#include <stdint.h>\n"
                "#include <time.h>\n"
                "#include <sched.h>\n"   # Fixes 'sched_yield' undeclared
                "#include <cstring>\n"
                "#include <cstdio>\n"
                "#undef bcopy\n"
                "#undef bzero\n"
            )
            if "<stddef.h>" not in content:
                file_path.write_text(injection + content)
                print(f"Injected system guards into: {file_path.name}")

    # 5. Fix size_t and 32-bit types in ultratypes.h
    ultratypes_h = include_path / "2.0L" / "PR" / "ultratypes.h"
    if ultratypes_h.exists():
        content = ultratypes_h.read_text()
        if "include <stddef.h>" not in content:
            content = content.replace(
                "#if defined(_LANGUAGE_C) || defined(_LANGUAGE_C_PLUS_PLUS)",
                "#if defined(_LANGUAGE_C) || defined(_LANGUAGE_C_PLUS_PLUS)\n#include <stddef.h>"
            )
            content = content.replace(
                "#if !defined(_SIZE_T) && !defined(_SIZE_T_) && !defined(_SIZE_T_DEF)",
                "#if !defined(_SIZE_T) && !defined(_SIZE_T_) && !defined(_SIZE_T_DEF) && defined(_MIPS_SZLONG)"
            )
        content = content.replace("typedef unsigned long\t\t\tu32;", "typedef unsigned int\t\t\tu32;")
        content = content.replace("typedef signed long\t\t\ts32;", "typedef signed int\t\t\ts32;")
        ultratypes_h.write_text(content)
        print("Patched: ultratypes.h")

    # 6. Fix bcopy/bzero conflict in os_libc.h
    os_libc_h = include_path / "2.0L" / "PR" / "os_libc.h"
    if os_libc_h.exists():
        content = os_libc_h.read_text()
        if "#undef bcopy" not in content:
            content = "#undef bcopy\n#undef bzero\n" + content
            os_libc_h.write_text(content)
            print("Patched: os_libc.h guards")

    # 7. Fix leafboat.c Array Initializer
    leafboat_c = cpp_dir / "game_src" / "BGS" / "ch" / "leafboat.c"
    if leafboat_c.exists():
        content = leafboat_c.read_text()
        old_code = "u8 tmp[6] = D_80390DA0;"
        new_code = "u8 tmp[6]; memcpy(tmp, D_80390DA0, 6);"
        if old_code in content:
            # Add include for memcpy if not present
            if 'include "game_string.h"' not in content and 'include <string.h>' not in content:
                content = '#include <string.h>\n' + content
            content = content.replace(old_code, new_code)
            leafboat_c.write_text(content)
            print("Patched: leafboat.c array initializer")

    # 8. Update resource_mgr.cpp to use decompress_rare_asset correctly
    res_mgr = cpp_dir / "emulator" / "resource_mgr.cpp"
    if res_mgr.exists():
        content = res_mgr.read_text()
        # Fix relative path
        content = content.replace('#include "../rare_decompression.h"', '#include "rare_decompression.h"')
        
        # Replace the problematic rare_decompress call with safe logic
        old_call = "rare_decompress(compressedBuf, (uint8_t*)dramAddr, size);"
        new_logic = (
            "uint32_t outSize = 0;\n"
            "        uint8_t* decomp = decompress_rare_asset(compressedBuf, size, &outSize);\n"
            "        if (decomp) {\n"
            "            memcpy(dramAddr, decomp, outSize);\n"
            "            free(decomp);\n"
            "        }"
        )
        if old_call in content:
            content = content.replace(old_call, new_logic)
            print("Patched: resource_mgr.cpp decompression logic")
            
        res_mgr.write_text(content)

def setup_build_dir():
    # Adjusted to point to the correct workspace root
    root_dir = Path(__file__).parent.parent
    cpp_dir = root_dir / "Android" / "app" / "src" / "main" / "cpp"
    
    # Origins (where your clean decomp files live)
    src_origin = root_dir / "decomp-files" / "src"
    include_origin = root_dir / "decomp-files" / "include"

    game_src_target = cpp_dir / "game_src"
    include_target = cpp_dir / "include"

    print(f"--- Preparing Source for Build ---")

    # Clean targets
    for folder in [game_src_target, include_target]:
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True, exist_ok=True)

    # Copy files
    if src_origin.exists():
        shutil.copytree(src_origin, game_src_target, dirs_exist_ok=True)
    else:
        print(f"CRITICAL: {src_origin} not found!")
        
    if include_origin.exists():
        shutil.copytree(include_origin, include_target, dirs_exist_ok=True)
    else:
        print(f"CRITICAL: {include_origin} not found!")

    patch_android_compatibility(cpp_dir)
    print(f"Done!")

if __name__ == "__main__":
    setup_build_dir()
