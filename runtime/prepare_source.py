import os
import shutil
import sys
from pathlib import Path

def patch_file(file_path, patch_map):
    """Replaces strings in a file based on a dictionary map."""
    if not file_path.exists():
        print(f"  [!] Missing for patch: {file_path.name}")
        return

    content = file_path.read_text(encoding='utf-8')
    original_content = content
    for search, replace in patch_map.items():
        content = content.replace(search, replace)

    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"  [✓] Patched: {file_path.name}")

def update_include_references(directory, rename_map):
    """Searches all files in a directory and updates #include references."""
    print(f"--- Updating Header References in {directory.name} ---")
    extensions = {'.c', '.h', '.cpp', '.s'}
    for file_path in directory.rglob('*'):
        if file_path.suffix in extensions:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                original = content
                for old_name, new_name in rename_map.items():
                    # Handle both quoted and angle bracket includes
                    content = content.replace(f'"{old_name}"', f'"{new_name}"')
                    content = content.replace(f'<{old_name}>', f'<{new_name}>')
                if content != original:
                    file_path.write_text(content, encoding='utf-8')
            except Exception as e:
                print(f"    [!] Failed to process {file_path.name}: {e}")

def inject_cpp_fixes(file_path):
    """Injects standard headers and wraps legacy headers safely."""
    if not file_path.exists(): return
    lines = file_path.read_text(encoding='utf-8').splitlines()
    if any('// ANDROID_FIX_GUARD' in line for line in lines[:10]): return

    # System headers MUST come first to define size_t, etc.
    new_content = [
        "// ANDROID_FIX_GUARD\n",
        "#include <stddef.h>\n",
        "#include <stdint.h>\n",
        "#include <stdio.h>\n",
        "#include <string.h>\n",
        "#include <stdlib.h>\n",
        "#include <sched.h>\n\n" # Critical for sched_yield
    ]

    for line in lines:
        if any(x in line for x in ["2.0L", "ultratypes.h", "gbi.h", "os.h"]) and "#include" in line:
            new_content.append('extern "C" {\n')
            new_content.append(line + "\n")
            new_content.append('}\n')
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

    # 1. SYNC
    print("--- Syncing Source ---")
    for source, target_name in [(src_origin, "game_src"), (include_origin, "include")]:
        target = cpp_root / target_name
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(source, target)

    # 2. RENAME SHADOW HEADERS (Critical for stdlib conflict)
    # We rename the game's headers so they don't block the system ones.
    shadow_map = {
        "string.h": "game_string.h", 
        "time.h": "game_time.h", 
        "stdlib.h": "game_stdlib.h",
        "sched.h": "game_sched.h" # Added to fix sched_yield conflict
    }
    for old_name, new_name in shadow_map.items():
        old_path = cpp_root / "include" / old_name
        if old_path.exists():
            old_path.rename(cpp_root / "include" / new_name)
            print(f"  [→] Renamed: {old_name} to {new_name}")

    update_include_references(cpp_root, shadow_map)

    # 3. FIX ULTRATYPES.H
    ultratypes = cpp_root / "include" / "2.0L" / "PR" / "ultratypes.h"
    patch_file(ultratypes, {
        "#ifndef _ULTRATYPES_H_": "#ifndef _ULTRATYPES_H_\n#include <stddef.h>\n#include <stdint.h>",
        "typedef unsigned long       u32;": "typedef uint32_t u32;",
        "typedef signed long         s32;": "typedef int32_t s32;",
        "typedef int bool;": "#ifndef __cplusplus\ntypedef int bool;\n#endif",
        "typedef unsigned int size_t;": "/* size_t from stddef.h */"
    })

    # 4. FIX OS_LIBC.H (The bcopy/bzero killer)
    # We #undef the Android macros before the game tries to declare them
    os_libc = cpp_root / "include" / "2.0L" / "PR" / "os_libc.h"
    patch_file(os_libc, {
        "extern void\tbcopy(const void *, void *, int);": "#undef bcopy\nextern void bcopy(const void *, void *, int);",
        "extern void\tbzero(void *, int);": "#undef bzero\nextern void bzero(void *, int);",
        "extern int\tbcmp(const void *, const void *, int);": "#undef bcmp\nextern int bcmp(const void *, const void *, int);"
    })

    # 5. FIX GBI.H
    gbi = cpp_root / "include" / "2.0L" / "PR" / "gbi.h"
    patch_file(gbi, {
        "#ifndef _GBI_H_": "#ifndef _GBI_H_\n#ifdef __cplusplus\nextern \"C\" {\n#endif",
        "#endif /* _GBI_H_ */": "#ifdef __cplusplus\n}\n#endif\n#endif"
    })

    # 6. INJECT INTO WRAPPERS
    for target in [
        cpp_root / "emulator" / "stubs.cpp", 
        cpp_root / "emulator" / "resource_mgr.cpp", 
        cpp_root / "ultra" / "NativeBridge.cpp"
    ]:
        inject_cpp_fixes(target)

    print("--- Preparation Complete ---")

if __name__ == "__main__":
    setup_build_dir()
