import os
import re
import sys

def patch_file(file_path, patch_map):
    """Replaces strings in a file based on a dictionary map."""
    if not os.path.exists(file_path):
        print(f"  [!] Missing: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    for search, replace in patch_map.items():
        content = content.replace(search, replace)
        
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [✓] Patched: {os.path.basename(file_path)}")

def inject_cpp_fixes(file_path):
    """Injects sched.h and wraps legacy headers in extern C blocks."""
    if not os.path.exists(file_path):
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Check if already patched to avoid nested extern "C" blocks
    if 'extern "C" {' in "".join(lines[:20]):
        print(f"  [-] Already patched: {os.path.basename(file_path)}")
        return

    new_content = ["#include <sched.h> // Fixed: sched_yield\n"]
    
    for line in lines:
        # Wrap N64-specific headers to prevent C++ name mangling conflicts
        if any(x in line for x in ["2.0L", "ultratypes.h", "gbi.h", "os.h"]) and "#include" in line:
            new_content.append('extern "C" {\n')
            new_content.append(line)
            new_content.append('}\n')
        else:
            new_content.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_content)
    print(f"  [✓] Injected C++ guards: {os.path.basename(file_path)}")

def main():
    # Detect the root directory (useful for GitHub Actions)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cpp_root = os.path.join(script_dir, "Android/app/src/main/cpp")
    
    if not os.path.exists(cpp_root):
        print(f"Error: Could not find CPP directory at {cpp_root}")
        sys.exit(1)

    print(f"--- Starting source preparation in: {cpp_root} ---")

    # 1. Fix sprintf linkage in the N64 OS header
    # This resolves the "different language linkage" error
    os_libc = os.path.join(cpp_root, "include/2.0L/PR/os_libc.h")
    patch_file(os_libc, {
        'extern int              sprintf(char *s, const char *fmt, ...);': 
        '#ifdef __cplusplus\nextern "C" {\n#endif\nextern int sprintf(char *s, const char *fmt, ...);\n#ifdef __cplusplus\n}\n#endif'
    })

    # 2. Fix ultratypes.h for 64-bit Android (long vs int)
    ultratypes = os.path.join(cpp_root, "include/2.0L/PR/ultratypes.h")
    patch_file(ultratypes, {
        "typedef unsigned long       u32;": "typedef unsigned int u32;",
        "typedef signed long         s32;": "typedef signed int s32;"
    })

    # 3. Fix C++ files that conflict with Android's <stdio.h>
    cpp_targets = [
        "emulator/stubs.cpp",
        "emulator/resource_mgr.cpp",
        "ultra/NativeBridge.cpp"
    ]
    for target in cpp_targets:
        inject_cpp_fixes(os.path.join(cpp_root, target))

    # 4. Handle Shadow Headers (Standard Library conflicts)
    # Renaming these prevents the compiler from picking them up instead of NDK headers
    shadow_headers = [
        ("include/string.h", "include/game_string.h"),
        ("include/time.h", "include/game_time.h")
    ]
    for old_name, new_name in shadow_headers:
        old_path = os.path.join(cpp_root, old_name)
        new_path = os.path.join(cpp_root, new_name)
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            print(f"  [✓] Renamed: {old_name} -> {new_name}")

    print("--- Preparation Complete ---")

if __name__ == "__main__":
    main()
