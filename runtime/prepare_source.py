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
    # Supports .c, .h, .cpp, .s
    extensions = {'.c', '.h', '.cpp', '.s'}
    
    for file_path in directory.rglob('*'):
        if file_path.suffix in extensions:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            original = content
            for old_name, new_name in rename_map.items():
                # Replace both "name.h" and <name.h> variants
                content = content.replace(f'"{old_name}"', f'"{new_name}"')
                content = content.replace(f'<{old_name}>', f'<{new_name}>')
            
            if content != original:
                file_path.write_text(content, encoding='utf-8')
                print(f"    [fixed] {file_path.relative_to(directory)}")

def inject_cpp_fixes(file_path):
    """Injects standard headers and wraps legacy headers safely."""
    if not file_path.exists():
        print(f"  [!] Target not found for injection: {file_path.name}")
        return

    lines = file_path.read_text(encoding='utf-8').splitlines()

    if any('// ANDROID_FIX_GUARD' in line for line in lines[:10]):
        print(f"  [-] Already guarded: {file_path.name}")
        return

    # 1. Start with System Headers FIRST (Proper C++ Linkage)
    new_content = [
        "// ANDROID_FIX_GUARD\n",
        "#include <stddef.h>\n",
        "#include <stdint.h>\n",
        "#include <stdio.h>\n",
        "#include <string.h>\n",
        "#include <sched.h>\n\n"
    ]

    for line in lines:
        # 2. Wrap N64-specific headers to prevent C++ name mangling
        # Only wrap if it's one of the legacy SDK files
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

    print(f"--- Environment Setup ---")
    if not src_origin.exists() or not include_origin.exists():
        print(f"  [!] Error: Ensure 'decomp-files' exists in {root_dir}")
        sys.exit(1)

    # 1. SYNC
    for source, target_name in [(src_origin, "game_src"), (include_origin, "include")]:
        target = cpp_root / target_name
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(source, target)
        print(f"  [→] Synced {target_name}")

    # 2. RENAME SHADOW HEADERS (Conflict Resolution)
    # We rename them so the compiler doesn't confuse them with NDK system headers
    shadow_map = {
        "string.h": "game_string.h",
        "time.h": "game_time.h",
        "stdlib.h": "game_stdlib.h" # Added for safety
    }
    
    for old_name, new_name in shadow_map.items():
        old_path = cpp_root / "include" / old_name
        if old_path.exists():
            new_path = cpp_root / "include" / new_name
            if new_path.exists(): os.remove(new_path)
            old_path.rename(new_path)
            print(f"  [✓] Renamed {old_name} -> {new_name}")

    # 3. UPDATE ALL REFERENCES TO RENAMED HEADERS
    update_include_references(cpp_root, shadow_map)

    # 4. PATCH LEGACY DEFINITIONS
    os_libc = cpp_root / "include" / "2.0L" / "PR" / "os_libc.h"
    patch_file(os_libc, {
        # Disable the internal sprintf to use the NDK's fortified version
        'extern int              sprintf(char *s, const char *fmt, ...);': 
        '#ifndef __ANDROID__\nextern int sprintf(char *s, const char *fmt, ...);\n#endif'
    })

    ultratypes = cpp_root / "include" / "2.0L" / "PR" / "ultratypes.h"
    patch_file(ultratypes, {
        "typedef unsigned long       u32;": "typedef unsigned int u32;",
        "typedef signed long         s32;": "typedef signed int s32;",
        "typedef int bool;": "#ifndef __cplusplus\ntypedef int bool;\n#endif",
        "typedef unsigned int size_t;": "/* size_t handled by stddef.h */"
    })

    # 5. INJECT GUARDS INTO WRAPPERS
    cpp_targets = [
        cpp_root / "emulator" / "stubs.cpp",
        cpp_root / "emulator" / "resource_mgr.cpp",
        cpp_root / "ultra" / "NativeBridge.cpp"
    ]
    for target in cpp_targets:
        inject_cpp_fixes(target)

    print("\n--- Preparation Complete. Ready to build. ---")

if __name__ == "__main__":
    setup_build_dir()
