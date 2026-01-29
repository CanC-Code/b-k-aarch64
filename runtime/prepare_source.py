import os
import shutil

def prepare_source():
    print("--- Syncing, Moving & Patching Source ---")

    # Paths
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"
    
    # CRITICAL: Do NOT sync tools directory as it would overwrite rare_decompression.cpp/h
    # The decomp-files/tools contains Python scripts, not the C++ decompression code
    # The C++ code is already in Android/app/src/main/cpp/tools and must be preserved
    sync_map = {"include": "include", "src": "src"}

    for src_sub, dest_sub in sync_map.items():
        full_src = os.path.join(src_root, src_sub)
        full_dest = os.path.join(android_cpp_path, dest_sub)
        if os.path.exists(full_src):
            if os.path.exists(full_dest): shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)
            print(f"  [→] Synced {src_sub}")

    print(f"  [!] Skipped tools sync (preserving C++ decompression code)")

    # Create ultra64 directory structure for compatibility
    base_include = os.path.join(android_cpp_path, "include")
    ultra64_dir = os.path.join(base_include, "ultra64")
    
    # Create ultra64 directory if it doesn't exist
    if not os.path.exists(ultra64_dir):
        os.makedirs(ultra64_dir)
        print(f"  [+] Created ultra64 directory")
    
    # Create a proper types.h in ultra64/
    # This needs to be a direct include without extern C since ultratypes.h handles that
    types_wrapper = """#ifndef _ULTRA64_TYPES_H_
#define _ULTRA64_TYPES_H_

#include "../2.0L/PR/ultratypes.h"

#endif /* _ULTRA64_TYPES_H_ */
"""
    types_dest = os.path.join(ultra64_dir, "types.h")
    with open(types_dest, 'w') as f:
        f.write(types_wrapper)
    print(f"  [→] Created ultra64/types.h wrapper")
    
    # CRITICAL FIX: We need to patch 2.0L/ultra64.h to include ultratypes.h at the top
    # Check if 2.0L/ultra64.h exists and prepend the types include
    ultra64_main = os.path.join(base_include, "2.0L", "ultra64.h")
    if os.path.exists(ultra64_main):
        with open(ultra64_main, 'r', errors='ignore') as f:
            content = f.read()
        
        # Check if ultratypes.h is not already included at the top
        if 'ultratypes.h' not in content[:200]:  # Check first 200 chars
            # Prepend the include after any existing header guards
            lines = content.split('\n')
            insert_pos = 0
            
            # Find position after header guards
            for i, line in enumerate(lines):
                if line.strip().startswith('#ifndef') or line.strip().startswith('#define'):
                    insert_pos = i + 1
                elif line.strip() and not line.strip().startswith('/*') and not line.strip().startswith('*'):
                    # Found first non-comment, non-guard line
                    break
            
            # Insert the types include
            lines.insert(insert_pos, '#include "PR/ultratypes.h"')
            
            with open(ultra64_main, 'w') as f:
                f.write('\n'.join(lines))
            print(f"  [✓] Patched 2.0L/ultra64.h to include ultratypes.h")
    
    # Create ultra64.h wrapper - much simpler now since 2.0L/ultra64.h has types
    ultra64_wrapper = """#ifndef _ULTRA64_ULTRA64_H_
#define _ULTRA64_ULTRA64_H_

#include "../2.0L/ultra64.h"

#endif /* _ULTRA64_ULTRA64_H_ */
"""
    ultra64_dest = os.path.join(ultra64_dir, "ultra64.h")
    with open(ultra64_dest, 'w') as f:
        f.write(ultra64_wrapper)
    print(f"  [→] Created ultra64/ultra64.h wrapper")

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
