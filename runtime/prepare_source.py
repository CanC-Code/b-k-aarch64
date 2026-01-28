import os
import shutil

def prepare_source():
    print("--- Syncing & Patching Source ---")

    # Target both the Android bridge and the decompiled source folders
    # Adjusted to ensure we hit the files before they are compiled
    target_dirs = [
        "Android/app/src/main/cpp",
        "decomp-files/include",
        "decomp-files/src"
    ]

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
    bridge_files = ["stubs.cpp", "resource_mgr.cpp", "NativeBridge.cpp", "pi_hle.cpp"]

    for base_path in target_dirs:
        if not os.path.exists(base_path):
            continue

        # PHASE 1: RECURSIVE RENAME
        for root, dirs, files in os.walk(base_path):
            for filename in files:
                if filename in renames:
                    old_path = os.path.join(root, filename)
                    new_path = os.path.join(root, renames[filename])
                    if os.path.exists(new_path):
                        os.remove(new_path)
                    shutil.move(old_path, new_path)
                    print(f"  [→] Renamed: {filename} to {renames[filename]}")

        # PHASE 2: RECURSIVE CONTENT PATCH
        for root, dirs, files in os.walk(base_path):
            for filename in files:
                if filename.endswith(('.c', '.cpp', '.h', '.hpp')):
                    file_path = os.path.join(root, filename)
                    with open(file_path, 'r', errors='ignore') as f:
                        content = f.read()
                    
                    original_content = content
                    for old_h, new_h in renames.items():
                        content = content.replace(f'#include <{old_h}>', f'#include <{new_h}>')
                        content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

                    if filename in bridge_files and "#ifdef __ANDROID__" not in content:
                        content = android_macro_fix + content

                    if content != original_content:
                        with open(file_path, 'w') as f:
                            f.write(content)
                        print(f"  [✓] Patched: {filename}")

if __name__ == "__main__":
    prepare_source()
