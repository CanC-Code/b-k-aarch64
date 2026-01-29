import os
import shutil

def prepare_source():
    print("--- Syncing, Moving & Patching Source ---")

    # Paths
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"

    # CRITICAL: Do NOT sync tools directory as it would overwrite rare_decompression.cpp/h
    sync_map = {"include": "include", "src": "src"}

    for src_sub, dest_sub in sync_map.items():
        full_src = os.path.join(src_root, src_sub)
        full_dest = os.path.join(android_cpp_path, dest_sub)
        if os.path.exists(full_src):
            if os.path.exists(full_dest): shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)
            print(f"  [→] Synced {src_sub}")

    print(f"  [!] Skipped tools sync (preserving C++ decompression code)")

    # Create ultra64 directory structure
    base_include = os.path.join(android_cpp_path, "include")
    ultra64_dir = os.path.join(base_include, "ultra64")

    if not os.path.exists(ultra64_dir):
        os.makedirs(ultra64_dir)
        print(f"  [+] Created ultra64 directory")

    # Create ultra64/types.h wrapper
    types_wrapper = """#ifndef _ULTRA64_TYPES_H_
#define _ULTRA64_TYPES_H_
#include "../2.0L/PR/ultratypes.h"
#endif"""
    with open(os.path.join(ultra64_dir, "types.h"), 'w') as f:
        f.write(types_wrapper)

    # Patch 2.0L/ultra64.h
    ultra64_main = os.path.join(base_include, "2.0L", "ultra64.h")
    if os.path.exists(ultra64_main):
        with open(ultra64_main, 'r', errors='ignore') as f:
            content = f.read()
        if 'ultratypes.h' not in content[:200]:
            lines = content.split('\n')
            lines.insert(2, '#include "PR/ultratypes.h"')
            with open(ultra64_main, 'w') as f:
                f.write('\n'.join(lines))
            print(f"  [✓] Patched 2.0L/ultra64.h")

    # Create ultra64.h wrapper
    ultra64_wrapper = """#ifndef _ULTRA64_ULTRA64_H_
#define _ULTRA64_ULTRA64_H_
#include "../2.0L/ultra64.h"
#endif"""
    with open(os.path.join(ultra64_dir, "ultra64.h"), 'w') as f:
        f.write(ultra64_wrapper)

    # Handle file renames
    renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            if filename in renames:
                shutil.move(os.path.join(root, filename), os.path.join(base_include, renames[filename]))

    # --- NEW: Patch os_libc.h for C++ Linkage ---
    os_libc_path = os.path.join(base_include, "2.0L", "PR", "os_libc.h")
    if os.path.exists(os_libc_path):
        with open(os_libc_path, 'r') as f:
            content = f.read()
        if 'extern "C"' not in content:
            patched = '#ifdef __cplusplus\\nextern "C" {\\n#endif\\n' + content + '\\n#ifdef __cplusplus\\n}\\n#endif'
            with open(os_libc_path, 'w') as f:
                f.write(patched)
            print(f"  [✓] Applied extern C wrapper to os_libc.h")

    # --- NEW: Neutralize bool.h Conflict ---
    bool_h_path = os.path.join(base_include, "bool.h")
    if os.path.exists(bool_h_path):
        modern_bool = "\\n#ifndef __cplusplus\\ntypedef int bool;\\n#define true 1\\n#define false 0\\n#endif\\n"
        with open(bool_h_path, 'r') as f:
            content = f.read()
        if "typedef int bool;" in content:
            new_content = content.replace("typedef int bool;", modern_bool).replace("#define true 1", "").replace("#define false 0", "")
            with open(bool_h_path, 'w') as f:
                f.write(new_content)
            print(f"  [✓] Neutralized C++ bool conflict in bool.h")

    # General Content Patching
    type_fix = '#include "ultra64/types.h"\\n' 
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            if filename.endswith(('.c', '.cpp', '.h')):
                path = os.path.join(root, filename)
                with open(path, 'r', errors='ignore') as f:
                    c = f.read()
                nc = c
                for old_h, new_h in renames.items():
                    nc = nc.replace(f'#include <{old_h}>', f'#include "{new_h}"').replace(f'#include "{old_h}"', f'#include "{new_h}"')
                if filename in renames.values() and 'types.h' not in nc:
                    nc = type_fix + nc
                if nc != c:
                    with open(path, 'w') as f: f.write(nc)

if __name__ == "__main__":
    prepare_source()
