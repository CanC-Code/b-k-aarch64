import os
import shutil
from pathlib import Path

def patch_file(file_path, patch_map):
    if not file_path.exists():
        print(f"  [!] Missing for patch: {file_path.name}")
        return
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    original_content = content
    for search, replace in patch_map.items():
        content = content.replace(search, replace)
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"  [✓] Patched: {file_path.name}")

def update_include_references(directory, rename_map):
    print(f"--- Updating Header References in {directory.name} ---")
    extensions = {'.c', '.h', '.cpp', '.s'}
    for file_path in directory.rglob('*'):
        if file_path.suffix in extensions:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                original = content
                for old_name, new_name in rename_map.items():
                    content = content.replace(f'"{old_name}"', f'"{new_name}"')
                    content = content.replace(f'<{old_name}>', f'<{new_name}>')
                if content != original:
                    file_path.write_text(content, encoding='utf-8')
            except Exception as e:
                print(f"    [!] Failed to process {file_path.name}: {e}")

def inject_cpp_fixes(file_path):
    if not file_path.exists(): return
    lines = file_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    if any('// ANDROID_FIX_GUARD' in line for line in lines[:10]): return

    # Force System headers to load before any legacy N64 headers
    new_content = [
        "// ANDROID_FIX_GUARD\n",
        "#include <stddef.h>\n",
        "#include <stdint.h>\n",
        "#include <stdio.h>\n",
        "#include <string.h>\n",
        "#include <stdlib.h>\n",
        "#include <sched.h>\n\n" 
    ]

    for line in lines:
        # Wrap legacy includes in extern "C"
        if any(x in line for x in ["2.0L", "ultratypes.h", "gbi.h", "os.h"]) and "#include" in line:
            new_content.append('extern "C" {\n' + line + '\n}\n')
        else:
            new_content.append(line + "\n")

    file_path.write_text("".join(new_content), encoding='utf-8')
    print(f"  [✓] Injected C++ guards: {file_path.name}")

def setup_build_dir():
    script_dir = Path(__file__).parent.resolve()
    root_dir = script_dir.parent
    cpp_root = root_dir / "Android" / "app" / "src" / "main" / "cpp"
    src_origin = root_dir / "decomp-files" / "src"
    include_origin = root_dir / "decomp-files" / "include"

    # 1. Sync
    print("--- Syncing Source ---")
    for source, target_name in [(src_origin, "game_src"), (include_origin, "include")]:
        target = cpp_root / target_name
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(source, target)

    # 2. Rename Shadow Headers
    shadow_map = {
        "string.h": "game_string.h", 
        "time.h": "game_time.h", 
        "stdlib.h": "game_stdlib.h",
        "sched.h": "game_sched.h"
    }
    for old_name, new_name in shadow_map.items():
        old_path = cpp_root / "include" / old_name
        if old_path.exists():
            dest = cpp_root / "include" / new_name
            if dest.exists(): os.remove(dest)
            old_path.rename(dest)
            print(f"  [→] Renamed: {old_name} to {new_name}")

    update_include_references(cpp_root, shadow_map)

    # 3. Fix Ultratypes (N64 types vs System types)
    patch_file(cpp_root / "include" / "2.0L" / "PR" / "ultratypes.h", {
        "#ifndef _ULTRATYPES_H_": "#ifndef _ULTRATYPES_H_\n#include <stddef.h>\n#include <stdint.h>",
        "typedef unsigned long       u32;": "typedef uint32_t u32;",
        "typedef signed long         s32;": "typedef int32_t s32;",
        "typedef int bool;": "#ifndef __cplusplus\ntypedef int bool;\n#endif",
        "typedef unsigned int size_t;": "/* size_t defined in stddef.h */"
    })

    # 4. Fix os_libc.h (Android macro conflict)
    # We undefine the macros so the extern "C" declarations don't error out
    patch_file(cpp_root / "include" / "2.0L" / "PR" / "os_libc.h", {
        "extern void\tbcopy": "#undef bcopy\nextern void bcopy",
        "extern void\tbzero": "#undef bzero\nextern void bzero",
        "extern int\tbcmp": "#undef bcmp\nextern int bcmp"
    })

    # 5. Fix GBI
    patch_file(cpp_root / "include" / "2.0L" / "PR" / "gbi.h", {
        "#ifndef _GBI_H_": "#ifndef _GBI_H_\n#ifdef __cplusplus\nextern \"C\" {\n#endif",
        "#endif /* _GBI_H_ */": "#ifdef __cplusplus\n}\n#endif\n#endif"
    })

    # 6. Final injection for C++ Wrappers
    for target in [
        cpp_root / "emulator" / "stubs.cpp", 
        cpp_root / "emulator" / "resource_mgr.cpp", 
        cpp_root / "ultra" / "NativeBridge.cpp",
        cpp_root / "ultra" / "otr_builder.cpp"
    ]:
        inject_cpp_fixes(target)

    print("--- Preparation Complete ---")

if __name__ == "__main__":
    setup_build_dir()
