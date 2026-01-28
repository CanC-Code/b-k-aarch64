import os
import shutil
from pathlib import Path

def patch_android_compatibility(cpp_dir):
    print("--- Applying Android Compatibility Patches ---")
    
    # 1. Rename Shadowing Headers
    # These names conflict with standard C++ headers
    shadow_headers = ["string.h", "stdio.h", "ctype.h", "stdlib.h"]
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
    # We must update every file to use the new #include "game_string.h"
    if renamed_map:
        print("Updating include references in all files...")
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

    # 4. Inject standard headers into bridge files
    # We do this AFTER renaming to ensure they get the SYSTEM headers
    wrapper_files = [
        cpp_dir / "ultra" / "NativeBridge.cpp",
        cpp_dir / "emulator" / "stubs.cpp"
    ]
    for file_path in wrapper_files:
        if file_path.exists():
            content = file_path.read_text()
            # We use <cstring> and <cstdio> here to explicitly ask for NDK versions
            injection = "#include <stddef.h>\n#include <stdint.h>\n#include <cstring>\n"
            if "<stddef.h>" not in content:
                file_path.write_text(injection + content)
                print(f"Injected system headers into: {file_path.name}")

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
    print(f"Done! Source synchronized and patched.")

if __name__ == "__main__":
    setup_build_dir()
