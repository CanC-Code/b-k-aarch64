import os
import shutil

def prepare_source():
    print("--- Syncing & Patching Source ---")
    
    # Configuration
    base_path = "Android/app/src/main/cpp"
    # Files that specifically need the Android Bionic macro fix
    bridge_files = [
        "emulator/stubs.cpp",
        "emulator/resource_mgr.cpp",
        "ultra/NativeBridge.cpp",
        "ultra/otr_builder.cpp"
    ]
    
    # Header collision mapping
    renames = {
        "string.h": "game_string.h",
        "time.h": "game_time.h",
        "stdlib.h": "game_stdlib.h",
        "sched.h": "game_sched.h"
    }

    # Macro fix for Android/N64 collision
    android_fix = """
#ifdef __ANDROID__
  #include <strings.h>
  #undef bcopy
  #undef bzero
  #undef bcmp
#endif
"""

    # 1. Physical Rename Phase
    # Search for these headers in the PR include directory and rename them
    pr_path = os.path.join(base_path, "include/2.0L/PR")
    if os.path.exists(pr_path):
        for old_name, new_name in renames.items():
            old_file = os.path.join(pr_path, old_name)
            new_file = os.path.join(pr_path, new_name)
            if os.path.exists(old_file):
                shutil.move(old_file, new_file)
                print(f"  [→] Renamed: {old_name} to {new_name}")

    # 2. Patching Phase
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if filename.endswith(('.c', '.cpp', '.h', '.hpp')):
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, base_path).replace("\\", "/")
                
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()

                original_content = content

                # Replace include references
                for old_h, new_h in renames.items():
                    content = content.replace(f'#include <{old_h}>', f'#include <{new_h}>')
                    content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

                # Inject Android fix for bridge files
                if rel_path in bridge_files:
                    if "#ifdef __ANDROID__" not in content:
                        content = android_fix + content

                if content != original_content:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"  [✓] Patched: {filename}")

if __name__ == "__main__":
    prepare_source()
