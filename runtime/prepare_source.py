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
                    content = fpath.read_text(errors='ignore')
                    changed = False
                    for old, new in renamed_map.items():
                        if f'#include "{old}"' in content:
                            content = content.replace(f'#include "{old}"', f'#include "{new}"')
                            changed = True
                    if changed:
                        fpath.write_text(content)

    # 3. Fix 'bool' redeclaration
    bool_h = include_path / "bool.h"
    if bool_h.exists():
        content = bool_h.read_text()
        if "ifndef __cplusplus" not in content:
            patched = content.replace("typedef int bool;", "#ifndef __cplusplus\ntypedef int bool;\n#endif")
            bool_h.write_text(patched)
            print("Patched: bool.h")

    # 4. Inject standard headers into bridge files (Fixed sched_yield)
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
                "#include <cstring>\n"
                "#include <cstdio>\n"
                "#include <sched.h>\n"  # Fixed: sched_yield error
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

    # 7. Fix relative path in resource_mgr.cpp
    res_mgr = cpp_dir / "emulator" / "resource_mgr.cpp"
    if res_mgr.exists():
        content = res_mgr.read_text()
        content = content.replace('#include "../rare_decompression.h"', '#include "rare_decompression.h"')
        res_mgr.write_text(content)

    # 8. Bulk Regex Fix for Array Initializations (leafboat.c, code_5DBC0.c, etc.)
    print("Scanning for invalid array initializations...")
    # Pattern looks for: u8 name[size] = D_LABEL;
    # It accounts for potential spaces and different array sizes/labels
    array_pattern = re.compile(r"u8\s+(\w+)\[(\d+)\]\s*=\s*(D_[0-9A-F_]+);")
    
    for root, _, files in os.walk(cpp_dir / "game_src"):
        for file in files:
            if file.endswith((".c", ".h")):
                fpath = Path(root) / file
                content = fpath.read_text(errors='ignore')
                
                if array_pattern.search(content):
                    # Replace with: u8 name[size]; memcpy(name, D_LABEL, size);
                    new_content = array_pattern.sub(r"u8 \1[\2]; memcpy(\1, \3, \2);", content)
                    
                    # Ensure memcpy is defined via string.h or our renamed game_string.h
                    if '<string.h>' not in new_content and '"game_string.h"' not in new_content:
                        new_content = '#include <string.h>\n' + new_content
                    
                    fpath.write_text(new_content)
                    print(f"Bulk Patched Array Init: {file}")

def setup_build_dir():
    root_dir = Path(__file__).parent.parent
    cpp_dir = root_dir / "Android" / "app" / "src" / "main" / "cpp"
    src_origin = root_dir / "decomp-files" / "src"
    include_origin = root_dir / "decomp-files" / "include"

    game_src_target = cpp_dir / "game_src"
    include_target = cpp_dir / "include"

    print(f"--- Preparing Source for Build ---")

    for folder in [game_src_target, include_target]:
        if folder.exists():
            shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True, exist_ok=True)

    if src_origin.exists():
        shutil.copytree(src_origin, game_src_target, dirs_exist_ok=True)
    if include_origin.exists():
        shutil.copytree(include_origin, include_target, dirs_exist_ok=True)

    patch_android_compatibility(cpp_dir)
    print(f"Done!")

if __name__ == "__main__":
    setup_build_dir()
