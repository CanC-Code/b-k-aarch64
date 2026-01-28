import os
import shutil

def prepare_source():
    print("--- Syncing & Patching Source ---")
    
    # Base path relative to repo root
    base_path = "Android/app/src/main/cpp"
    
    # Specific files needing the Android Bionic macro fix
    bridge_files = [
        "emulator/stubs.cpp",
        "emulator/resource_mgr.cpp",
        "ultra/NativeBridge.cpp",
        "ultra/otr_builder.cpp"
    ]
    
    # Headers that conflict with Android System headers
    renames = {
        "string.h": "game_string.h",
        "time.h": "game_time.h",
        "stdlib.h": "game_stdlib.h",
        "sched.h": "game_sched.h"
    }

    android_macro_fix = """
#ifdef __ANDROID__
  #include <strings.h>
  #undef bcopy
  #undef bzero
  #undef bcmp
#endif
"""

    # 1. Recursive Rename Phase
    # This ensures we find the files even if they are in include/ or include/PR/
    include_root = os.path.join(base_path, "include")
    if os.path.exists(include_root):
        for root, dirs, files in os.walk(include_root):
            for filename in files:
                if filename in renames:
                    old_file = os.path.join(root, filename)
                    new_file = os.path.join(root, renames[filename])
                    
                    # Clean up old renamed file if it exists, then move
                    if os.path.exists(new_file):
                        os.remove(new_file)
                    shutil.move(old_file, new_file)
                    print(f"  [→] Renamed: {filename} to {renames[filename]}")

    # 2. Patching Phase
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if filename.endswith(('.c', '.cpp', '.h', '.hpp')):
                file_path = os.path.join(root, filename)
                
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                
                original_content = content

                # Global Search & Replace for renamed includes
                for old_h, new_h in renames.items():
                    content = content.replace(f'#include <{old_h}>', f'#include <{new_h}>')
                    content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

                # Inject the Android Macro Fix for Bionic compatibility
                rel_path = os.path.relpath(file_path, base_path).replace("\\", "/")
                if rel_path in bridge_files:
                    if "#ifdef __ANDROID__" not in content:
                        content = android_macro_fix + content

                if content != original_content:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"  [✓] Patched: {filename}")

if __name__ == "__main__":
    prepare_source()
