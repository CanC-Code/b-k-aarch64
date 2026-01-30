import os
import shutil
import re

def prepare_source():
    print("--- Syncing, Moving & Patching Source ---")
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"
    sync_map = {"include": "include", "src": "src"}

    # 1. Initial Sync: Ensure fresh source from decomp workspace
    for src_sub, dest_sub in sync_map.items():
        full_src = os.path.join(src_root, src_sub)
        full_dest = os.path.join(android_cpp_path, dest_sub)
        if os.path.exists(full_src):
            if os.path.exists(full_dest): shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)

    base_include = os.path.join(android_cpp_path, "include")

    # 2. Fix ultratypes.h with polite guards
    ultratypes_path = os.path.join(base_include, "2.0L", "PR", "ultratypes.h")
    if os.path.exists(ultratypes_path):
        with open(ultratypes_path, 'r') as f:
            content = f.read()
        if "#ifndef _ULTRATYPES_H_GUARD" not in content:
            patched = "#ifndef _ULTRATYPES_H_GUARD\n#define _ULTRATYPES_H_GUARD\n" + content + "\n#endif"
            with open(ultratypes_path, 'w') as f: f.write(patched)
            print("  [✓] Applied redefinition guards to ultratypes.h")

    # 3. Resolve C++ bool keyword conflict
    bool_h_path = os.path.join(base_include, "bool.h")
    if os.path.exists(bool_h_path):
        modern_bool = "#ifndef __cplusplus\n#ifndef bool\ntypedef int bool;\n#define true 1\n#define false 0\n#endif\n#endif\n"
        with open(bool_h_path, 'w') as f: f.write(modern_bool)
        print("  [✓] Resolved C++ bool keyword conflict")

    # 4. Safe Renaming & Global Patching
    renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
    
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            path = os.path.join(root, filename)
            if filename in renames:
                new_path = os.path.join(base_include, renames[filename])
                shutil.move(path, new_path)

    # 5. Global Patching with Regex Word Boundaries
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            path = os.path.join(root, filename)
            if filename.endswith(('.c', '.cpp', '.h')):
                with open(path, 'r', errors='ignore') as f: orig = f.read()
                
                updated = orig
                for old_h, new_h in renames.items():
                    updated = updated.replace(f'#include <{old_h}>', f'#include "{new_h}"')
                    updated = updated.replace(f'#include "{old_h}"', f'#include "{new_h}"')
                
                # FIXED: Use regex word boundaries to avoid corrupting enum names
                updated = re.sub(r'\bUNUSED\b', '[[maybe_unused]]', updated)

                if updated != orig:
                    with open(path, 'w') as f: f.write(updated)

if __name__ == "__main__":
    prepare_source()
