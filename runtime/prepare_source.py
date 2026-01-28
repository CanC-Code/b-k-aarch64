import os
import shutil

def prepare_source():
    print("--- Syncing & Patching Source ---")
    
    # Target the directory containing all C++ source
    base_path = "Android/app/src/main/cpp"
    
    # N64 headers that conflict with Android/Linux system headers
    renames = {
        "string.h": "game_string.h",
        "time.h": "game_time.h",
        "stdlib.h": "game_stdlib.h",
        "sched.h": "game_sched.h"
    }

    # Macro fix for Android Bionic compatibility
    android_macro_fix = """
#ifdef __ANDROID__
  #include <strings.h>
  #undef bcopy
  #undef bzero
  #undef bcmp
#endif
"""
    bridge_files = ["stubs.cpp", "resource_mgr.cpp", "NativeBridge.cpp", "otr_builder.cpp"]

    # PHASE 1: RECURSIVE RENAME
    # This finds the files anywhere under the base_path and renames them physicaly
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if filename in renames:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, renames[filename])
                
                # Perform the physical rename on disk
                if os.path.exists(new_path):
                    os.remove(new_path)
                shutil.move(old_path, new_path)
                print(f"  [→] Renamed File: {filename} to {renames[filename]}")

    # PHASE 2: RECURSIVE CONTENT PATCH
    # This updates the #include lines inside the files
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if filename.endswith(('.c', '.cpp', '.h', '.hpp')):
                file_path = os.path.join(root, filename)
                
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                
                original_content = content

                # Replace header references
                for old_h, new_h in renames.items():
                    content = content.replace(f'#include <{old_h}>', f'#include <{new_h}>')
                    content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

                # Inject Android fix for specific bridge files
                if filename in bridge_files and "#ifdef __ANDROID__" not in content:
                    content = android_macro_fix + content

                if content != original_content:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"  [✓] Patched Content: {filename}")

if __name__ == "__main__":
    prepare_source()
