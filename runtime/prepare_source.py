import os
import shutil

def prepare_source():
    print("--- Syncing & Patching Source ---")
    
    # Root path for Android C++ files
    base_path = "Android/app/src/main/cpp"
    
    # Map of N64 headers that conflict with Android System/Bionic headers
    renames = {
        "string.h": "game_string.h",
        "time.h": "game_time.h",
        "stdlib.h": "game_stdlib.h",
        "sched.h": "game_sched.h"
    }

    # Macro fix for Android Bionic compatibility (prevents bcopy/bzero conflicts)
    android_macro_fix = """
#ifdef __ANDROID__
  #include <strings.h>
  #undef bcopy
  #undef bzero
  #undef bcmp
#endif
"""
    # Files that specifically need the macro fix injected
    bridge_files = ["stubs.cpp", "resource_mgr.cpp", "NativeBridge.cpp", "otr_builder.cpp"]

    # --- PHASE 1: RECURSIVE RENAME ---
    # We walk the entire tree to find these headers wherever they are
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if filename in renames:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, renames[filename])
                
                # Perform the rename
                if os.path.exists(new_path):
                    os.remove(new_path)
                shutil.move(old_path, new_path)
                # Success log should appear in your GitHub Action log now:
                print(f"  [→] Renamed: {old_path} -> {renames[filename]}")

    # --- PHASE 2: GLOBAL PATCHING ---
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if filename.endswith(('.c', '.cpp', '.h', '.hpp')):
                file_path = os.path.join(root, filename)
                
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                
                original_content = content

                # Replace header references to the new renamed versions
                for old_h, new_h in renames.items():
                    content = content.replace(f'#include <{old_h}>', f'#include <{new_h}>')
                    content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

                # Inject Android Bionic fix if it's a bridge file
                if filename in bridge_files and "#ifdef __ANDROID__" not in content:
                    content = android_macro_fix + content

                if content != original_content:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"  [✓] Patched: {filename}")

if __name__ == "__main__":
    prepare_source()
