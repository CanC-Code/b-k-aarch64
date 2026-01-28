import os
import shutil
from pathlib import Path

def patch_android_compatibility(cpp_dir):
    """Applies clean injections to solve NDK/C++ conflicts."""
    print("--- Applying Android Compatibility Patches ---")
    
    # Fix 1: Resolve 'bool' redeclaration in C++
    bool_h = cpp_dir / "include" / "bool.h"
    if bool_h.exists():
        content = bool_h.read_text()
        if "ifndef __cplusplus" not in content:
            # Wrap the typedef so it only applies to C, not C++
            patched = content.replace(
                "typedef int bool;",
                "#ifndef __cplusplus\ntypedef int bool;\n#endif"
            )
            bool_h.write_text(patched)
            print(f"Patched: {bool_h.name} (C++ bool conflict fixed)")

    # Fix 2: Inject standard headers into wrapper files that need them
    # This prevents the 'unknown type name size_t' errors
    wrapper_files = [
        cpp_dir / "emulator" / "stubs.cpp",
        cpp_dir / "ultra" / "NativeBridge.cpp",
        cpp_dir / "emulator" / "resource_mgr.cpp"
    ]
    
    for file_path in wrapper_files:
        if file_path.exists():
            content = file_path.read_text()
            if "<stddef.h>" not in content:
                # Add these at the very top
                patched = "#include <stddef.h>\n#include <stdint.h>\n" + content
                file_path.write_text(patched)
                print(f"Patched: {file_path.name} (Injected stddef.h/stdint.h)")

def setup_build_dir():
    root_dir = Path(__file__).parent.parent
    cpp_dir = root_dir / "Android" / "app" / "src" / "main" / "cpp"

    src_origin = root_dir / "decomp-files" / "src"
    include_origin = root_dir / "decomp-files" / "include"

    game_src_target = cpp_dir / "game_src"
    include_target = cpp_dir / "include"

    print(f"--- Preparing Source for Build ---")

    # 1. Clean and recreate
    for folder in [game_src_target, include_target]:
        if folder.exists():
            print(f"Cleaning existing directory: {folder}")
            shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True, exist_ok=True)

    # 2. Copy source files
    if src_origin.exists():
        print(f"Copying source: {src_origin} -> {game_src_target}")
        shutil.copytree(src_origin, game_src_target, dirs_exist_ok=True)
    else:
        print(f"CRITICAL ERROR: Source origin {src_origin} not found!")
        exit(1)

    # 3. Copy headers
    if include_origin.exists():
        print(f"Copying headers: {include_origin} -> {include_target}")
        shutil.copytree(include_origin, include_target, dirs_exist_ok=True)
    else:
        print(f"CRITICAL ERROR: Include origin {include_origin} not found!")
        exit(1)

    # 4. Injected Fixes
    # We pass the parent cpp_dir so it can find both include/ and emulator/ folders
    patch_android_compatibility(cpp_dir)

    print(f"Done! Source synchronized and patched for Android.")

if __name__ == "__main__":
    setup_build_dir()
