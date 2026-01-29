import os
import shutil

def prepare_source():
    print("--- Syncing, Moving & Patching Source ---")
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"
    sync_map = {"include": "include", "src": "src"}

    for src_sub, dest_sub in sync_map.items():
        full_src = os.path.join(src_root, src_sub)
        full_dest = os.path.join(android_cpp_path, dest_sub)
        if os.path.exists(full_src):
            if os.path.exists(full_dest): shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)

    base_include = os.path.join(android_cpp_path, "include")
    
    # 1. Fix os_libc.h Linkage & Macro Conflicts
    os_libc_path = os.path.join(base_include, "2.0L", "PR", "os_libc.h")
    if os.path.exists(os_libc_path):
        with open(os_libc_path, 'r') as f:
            content = f.read()
        if 'extern "C"' not in content:
            # Wrap in extern C AND undefine system macros that conflict
            patched = """#ifndef _OS_LIBC_PATCH_H
#define _OS_LIBC_PATCH_H
#include <strings.h>
#undef bcopy
#undef bzero
#undef bcmp
#ifdef __cplusplus
extern "C" {
#endif
""" + content + """
#ifdef __cplusplus
}
#endif
#endif"""
            with open(os_libc_path, 'w') as f:
                f.write(patched)

    # 2. Correctly fix bool.h
    bool_h_path = os.path.join(base_include, "bool.h")
    if os.path.exists(bool_h_path):
        modern_bool = """
#ifndef __cplusplus
typedef int bool;
#define true 1
#define false 0
#endif
"""
        with open(bool_h_path, 'w') as f:
            f.write(modern_bool)

    # 3. Handle renames and fix content
    renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            path = os.path.join(root, filename)
            if filename in renames:
                shutil.move(path, os.path.join(base_include, renames[filename]))
            
            if filename.endswith(('.c', '.cpp', '.h')):
                with open(path, 'r', errors='ignore') as f:
                    c = f.read()
                nc = c
                for old_h, new_h in renames.items():
                    nc = nc.replace(f'#include <{old_h}>', f'#include "{new_h}"')
                    nc = nc.replace(f'#include "{old_h}"', f'#include "{new_h}"')
                
                # Ensure game_string.h has proper guards if patched
                if filename == "game_string.h" and 'ultra64/types.h' not in nc:
                    nc = '#include "ultra64/types.h"\n' + nc
                
                if nc != c:
                    with open(path, 'w') as f: f.write(nc)

if __name__ == "__main__":
    prepare_source()
