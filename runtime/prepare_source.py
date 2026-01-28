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
                        content = fpath.read_text(encoding='utf-8', errors='ignore')
                        changed = False
                        for old, new in renamed_map.items():
                            pattern = f'#include "{old}"'
                            if pattern in content:
                                content = content.replace(pattern, f'#include "{new}"')
                                changed = True
                        if changed:
                            fpath.write_text(content, encoding='utf-8')
                    except Exception as e:
                        print(f"Failed to process {file}: {e}")

    # 3. Fix 'bool' redeclaration and basic types
    bool_h = include_path / "bool.h"
    if bool_h.exists():
        content = bool_h.read_text()
        if "#ifndef __cplusplus" not in content:
            patched = content.replace("typedef int bool;", "#ifndef __cplusplus\ntypedef int bool;\n#endif")
            bool_h.write_text(patched)
            print("Patched: bool.h")

    # 4. Inject standard headers into bridge files
    # _GNU_SOURCE must be defined BEFORE any standard headers are included.
    wrapper_files = [
        cpp_dir / "ultra" / "NativeBridge.cpp",
        cpp_dir / "emulator" / "stubs.cpp",
        cpp_dir / "emulator" / "resource_mgr.cpp"
    ]
    injection = (
        "#ifndef _GNU_SOURCE\n"
        "#define _GNU_SOURCE\n"
        "#endif\n"
        "#include <sched.h>\n" 
        "#include <stddef.h>\n"
        "#include <stdint.h>\n"
        "#include <time.h>\n"
        "#include <cstring>\n"
        "#include <cstdio>\n"
        "#undef bcopy\n"
        "#undef bzero\n"
    )
    for file_path in wrapper_files:
        if file_path.exists():
            content = file_path.read_text()
            if "_GNU_SOURCE" not in content:
                file_path.write_text(injection + content)
                print(f"Injected system guards into: {file_path.name}")

    # 5. Fix size_t and 32-bit types (64-bit portability)
    ultratypes_h = include_path / "2.0L" / "PR" / "ultratypes.h"
    if ultratypes_h.exists():
        content = ultratypes_h.read_text()
        content = content.replace("typedef unsigned long\t\t\tu32;", "typedef unsigned int\t\t\tu32;")
        content = content.replace("typedef signed long\t\t\ts32;", "typedef signed int\t\t\ts32;")
        if "include <stddef.h>" not in content:
            content = content.replace(
                "#if defined(_LANGUAGE_C) || defined(_LANGUAGE_C_PLUS_PLUS)",
                "#include <stddef.h>\n#if defined(_LANGUAGE_C) || defined(_LANGUAGE_C_PLUS_PLUS)"
            )
        ultratypes_h.write_text(content)
        print("Patched: ultratypes.h for 64-bit portability")

    # 6. Fix bcopy/bzero conflict
    os_libc_h = include_path / "2.0L" / "PR" / "os_libc.h"
    if os_libc_h.exists():
        content = os_libc_h.read_text()
        if "#undef bcopy" not in content:
            content = "#undef bcopy\n#undef bzero\n" + content
            os_libc_h.write_text(content)
            print("Patched: os_libc.h guards")

    # 7. Array Initialization Fix
    print("Scanning for invalid array initializations...")
    array_pattern = re.compile(r"u8\s+(\w+)\[(\d+)\]\s*=\s*(D_[0-9A-F_]+);")

    for root, _, files in os.walk(cpp_dir / "game_src"):
        for file in files:
            if file.endswith((".c", ".h")):
                fpath = Path(root) / file
                content = fpath.read_text(errors='ignore')
                if array_pattern.search(content):
                    new_content = array_pattern.sub(r"u8* \1 = (u8*)&\3;", content)
                    fpath.write_text(new_content)
                    print(f"Fixed Global Array Init: {file}")

def setup_build_dir():
    root_dir = Path(__file__).parent.parent
    cpp_dir = root_dir / "Android" / "app" / "src" / "main" / "cpp"
    src_origin = root_dir / "decomp-files" / "src"
    include_origin = root_dir / "decomp-files" / "include"

    print(f"--- Preparing Source for Build ---")
    for target, origin in [(cpp_dir / "game_src", src_origin), (cpp_dir / "include", include_origin)]:
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
        if origin.exists():
            shutil.copytree(origin, target, dirs_exist_ok=True)

    patch_android_compatibility(cpp_dir)
    print(f"Build directory ready!")

if __name__ == "__main__":
    setup_build_dir()
