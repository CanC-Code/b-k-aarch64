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

    # Create ultra64 directory structure for compatibility
    base_include = os.path.join(android_cpp_path, "include")
    ultra64_dir = os.path.join(base_include, "ultra64")
    
    # Create ultra64 directory if it doesn't exist
    if not os.path.exists(ultra64_dir):
        os.makedirs(ultra64_dir)
        print(f"  [+] Created ultra64 directory")
    
    # Copy types.h from 2.0L/PR to ultra64/
    types_source = os.path.join(base_include, "2.0L", "PR", "ultratypes.h")
    types_dest = os.path.join(ultra64_dir, "types.h")
    if os.path.exists(types_source):
        shutil.copy2(types_source, types_dest)
        print(f"  [→] Copied ultratypes.h to ultra64/types.h")
    
    # Also copy ultra64.h as a fallback
    ultra64_source = os.path.join(base_include, "2.0L", "ultra64.h")
    ultra64_dest = os.path.join(ultra64_dir, "ultra64.h")
    if os.path.exists(ultra64_source):
        shutil.copy2(ultra64_source, ultra64_dest)
        print(f"  [→] Copied ultra64.h to ultra64/")

    renames = {
        "string.h": "game_string.h",
        "time.h": "game_time.h",
        "sched.h": "game_sched.h"
    }

    # PHASE 1: Physical Renaming and "Promotion"
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            if filename in renames:
                new_name = renames[filename]
                old_path = os.path.join(root, filename)
                new_path = os.path.join(base_include, new_name)
                if old_path != new_path:  # Avoid moving to itself
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
                
                # Replace old header includes with new names
                for old_h, new_h in renames.items():
                    new_content = new_content.replace(f'#include <{old_h}>', f'#include "{new_h}"')
                    new_content = new_content.replace(f'#include "{old_h}"', f'#include "{new_h}"')
                
                # Fix rare_decompression.h includes - make them consistent
                new_content = new_content.replace(
                    '#include "../tools/rare_decompression.h"',
                    '#include "rare_decompression.h"'
                )
                
                # If this is one of our renamed system headers, ensure it has types
                if filename in renames.values() and 'types.h' not in new_content:
                    new_content = type_fix + new_content

                if new_content != content:
                    with open(file_path, 'w') as f:
                        f.write(new_content)
                    print(f"  [✓] Patched {filename}")

if __name__ == "__main__":
    prepare_source()
