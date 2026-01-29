import os
import shutil

def prepare_source():
    print("--- Syncing, Moving & Patching Source ---")

    # Paths
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"
    
    # 1. Sync files from decomp-files to Android project
    sync_map = {
        "include": "include",
        "src": "src",
        "tools": "tools"
    }

    for src_sub, dest_sub in sync_map.items():
        full_src = os.path.join(src_root, src_sub)
        full_dest = os.path.join(android_cpp_path, dest_sub)
        
        if os.path.exists(full_src):
            if os.path.exists(full_dest):
                shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)
            print(f"  [→] Synced {src_sub} to Android directory")

    # 2. Define renames to avoid NDK system conflicts
    renames = {
        "string.h": "game_string.h",
        "time.h": "game_time.h",
        "stdlib.h": "game_stdlib.h",
        "sched.h": "game_sched.h"
    }

    # 3. Patching and Renaming
    base_include = os.path.join(android_cpp_path, "include")
    
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            # Physical Rename
            if filename in renames:
                old_path = os.path.join(root, filename)
                new_name = renames[filename]
                new_path = os.path.join(root, new_name)
                
                shutil.move(old_path, new_path)
                
                # Promotion: Move the renamed header to the root include dir 
                # so the compiler's include path finds it easily.
                final_dest = os.path.join(base_include, new_name)
                if new_path != final_dest:
                    if os.path.exists(final_dest): os.remove(final_dest)
                    shutil.move(new_path, final_dest)
                
                print(f"  [!] Renamed & Promoted {filename} -> {new_name}")
                continue 

            # Content Revision (Update #include lines)
            if filename.endswith(('.c', '.cpp', '.h', '.hpp')):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                
                new_content = content
                for old_h, new_h in renames.items():
                    new_content = new_content.replace(f'#include <{old_h}>', f'#include <{new_h}>')
                    new_content = new_content.replace(f'#include "{old_h}"', f'#include "{new_h}"')
                
                if new_content != content:
                    with open(file_path, 'w') as f:
                        f.write(new_content)
                    print(f"  [✓] Patched {filename}")

if __name__ == "__main__":
    prepare_source()
