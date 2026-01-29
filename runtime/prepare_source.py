import os
import shutil

def prepare_source():
    print("--- Syncing, Moving & Patching Source ---")
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"
    sync_map = {"include": "include", "src": "src"}

    # 1. Initial Sync
    for src_sub, dest_sub in sync_map.items():
        full_src = os.path.join(src_root, src_sub)
        full_dest = os.path.join(android_cpp_path, dest_sub)
        if os.path.exists(full_src):
            if os.path.exists(full_dest): shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)

    base_include = os.path.join(android_cpp_path, "include")
    
    # 2. Fix os_libc.h Macro/Linkage Conflict (CRITICAL)
    # Undefine bcopy/bzero before the N64 SDK tries to declare them as functions
    os_libc_path = os.path.join(base_include, "2.0L", "PR", "os_libc.h")
    if os.path.exists(os_libc_path):
        with open(os_libc_path, 'r') as f:
            content = f.read()
        if 'extern "C"' not in content:
            patched_content = (
                "#ifndef _OS_LIBC_PATCH_H\n"
                "#define _OS_LIBC_PATCH_H\n"
                "#include <strings.h>\n"
                "#undef bcopy\n"
                "#undef bzero\n"
                "#undef bcmp\n"
                "#ifdef __cplusplus\n"
                "extern \"C\" {\n"
                "#endif\n\n"
                f"{content}\n\n"
                "#ifdef __cplusplus\n"
                "}\n"
                "#endif\n"
                "#endif\n"
            )
            with open(os_libc_path, 'w') as f:
                f.write(patched_content)
            print("  [✓] Applied macro conflict fixes to os_libc.h")

    # 3. Handle C++ bool Redefinition
    bool_h_path = os.path.join(base_include, "bool.h")
    if os.path.exists(bool_h_path):
        modern_bool = (
            "#ifndef __cplusplus\n"
            "typedef int bool;\n"
            "#define true 1\n"
            "#define false 0\n"
            "#endif\n"
        )
        with open(bool_h_path, 'w') as f:
            f.write(modern_bool)
        print("  [✓] Resolved C++ bool conflict")

    # 4. Safe Renaming & Include Patching
    renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
    
    # Move files first to avoid FileNotFoundError during patching
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            if filename in renames:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(base_include, renames[filename])
                shutil.move(old_path, new_path)

    # Patch content across all relevant source/header files
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            path = os.path.join(root, filename)
            if filename.endswith(('.c', '.cpp', '.h')):
                with open(path, 'r', errors='ignore') as f:
                    orig = f.read()
                
                updated = orig
                # Update include paths for renamed headers
                for old_h, new_h in renames.items():
                    updated = updated.replace(f'#include <{old_h}>', f'#include "{new_h}"')
                    updated = updated.replace(f'#include "{old_h}"', f'#include "{new_h}"')
                
                # Ensure game_string.h has essential ultratypes
                if filename == "game_string.h" and 'ultratypes.h' not in updated:
                    updated = '#include "2.0L/PR/ultratypes.h"\n' + updated
                
                if updated != orig:
                    with open(path, 'w') as f:
                        f.write(updated)

if __name__ == "__main__":
    prepare_source()
