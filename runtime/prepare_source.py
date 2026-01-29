import os
import shutil

def prepare_source():
    print("--- Syncing, Moving & Patching Source ---")

    # Paths
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"
    
    sync_map = {"include": "include", "src": "src", "tools": "tools"}

    for src_sub, dest_sub in sync_map.items():
        full_src = os.path.join(src_root, src_sub)
        full_dest = os.path.join(android_cpp_path, dest_sub)
        if os.path.exists(full_src):
            if os.path.exists(full_dest): shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)
            print(f"  [→] Synced {src_sub}")

    renames = {
        "string.h": "game_string.h",
        "time.h": "game_time.h",
        "stdlib.h": "game_stdlib.h",
        "sched.h": "game_sched.h"
    }

    base_include = os.path.join(android_cpp_path, "include")

    # PHASE 1: Physical Renaming and "Promotion"
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            # Fix for rare_decompression.h: Promote it to root include
            if filename == "rare_decompression.h":
                target = os.path.join(base_include, filename)
                if os.path.join(root, filename) != target:
                    shutil.copy2(os.path.join(root, filename), target)
                    print(f"  [!] Promoted {filename} to include root")

            if filename in renames:
                new_name = renames[filename]
                old_path = os.path.join(root, filename)
                new_path = os.path.join(base_include, new_name)
                shutil.move(old_path, new_path)
                print(f"  [!] Renamed & Promoted {filename} -> {new_name}")

    # PHASE 2: Content Patching
    # We inject types.h into the renamed headers to fix the 'u8' errors
    type_fix = '#include "ultra64/types.h"\n' 

    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            if filename.endswith(('.c', '.cpp', '.h', '.hpp')):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                
                new_content = content
                for old_h, new_h in renames.items():
                    new_content = new_content.replace(f'#include <{old_h}>', f'#include <{new_h}>')
                    new_content = new_content.replace(f'#include "{old_h}"', f'#include "{new_h}"')
                
                # If this is one of our renamed system headers, ensure it has types
                if filename in renames.values() and 'types.h' not in new_content:
                    new_content = type_fix + new_content

                if new_content != content:
                    with open(file_path, 'w') as f:
                        f.write(new_content)
                    print(f"  [✓] Patched {filename}")

if __name__ == "__main__":
    prepare_source()
