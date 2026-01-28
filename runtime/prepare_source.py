import os
import shutil

def prepare_source():
    print("--- Syncing & Patching Source ---")
    
    # This path is relative to the root of your repo
    base_path = "Android/app/src/main/cpp"
    
    # Relative paths from base_path for patching
    bridge_files = [
        "emulator/stubs.cpp",
        "emulator/resource_mgr.cpp",
        "ultra/NativeBridge.cpp",
        "ultra/otr_builder.cpp"
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

    # 1. Physical Rename Phase
    pr_path = os.path.join(base_path, "include/2.0L/PR")
    if os.path.exists(pr_path):
        for old, new in renames.items():
            old_file = os.path.join(pr_path, old)
            new_file = os.path.join(pr_path, new)
            if os.path.exists(old_file):
                if os.path.exists(new_file): os.remove(new_file)
                shutil.move(old_file, new_file)
                print(f"  [→] Renamed: {old} to {new}")

    # 2. Search and Patch Phase
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if filename.endswith(('.c', '.cpp', '.h', '.hpp')):
                file_path = os.path.join(root, filename)
                
                # Read content
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                
                original_content = content

                # Update includes
                for old_h, new_h in renames.items():
                    content = content.replace(f'#include <{old_h}>', f'#include <{new_h}>')
                    content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

                # Inject Android fix if file is in bridge_files
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
