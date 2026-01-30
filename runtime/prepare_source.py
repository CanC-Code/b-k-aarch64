import os
import shutil
import re

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

    # 2. Fix game_string.h & core1/mem.h - Comment out conflicting overrides
    # These functions conflict with Android's built-in string.h
    files_to_patch = [
        os.path.join(base_include, "game_string.h"),
        os.path.join(base_include, "core1", "mem.h")
    ]
    
    conflicting_funcs = ['strcat', 'strcpy', 'strlen', 'memcpy', 'memmove', 'wmemcpy']

    for file_path in files_to_patch:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            for func in conflicting_funcs:
                # Matches: void strcat(char *dst, char *src); (and variants)
                content = re.sub(rf'(?m)^.*?\b{func}\b.*?;', r'// \g<0>', content)

            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  [✓] Commented out conflicting functions in {os.path.basename(file_path)}")

    # 3. Handle C++ bool Redefinition
    bool_h_path = os.path.join(base_include, "bool.h")
    if os.path.exists(bool_h_path):
        modern_bool = (
            "#ifndef __cplusplus\n#ifndef bool\ntypedef int bool;\n#define true 1\n#define false 0\n#endif\n#endif\n"
        )
        with open(bool_h_path, 'w') as f:
            f.write(modern_bool)

    # 4. Correct UNUSED attribute for C files
    # Replacing [[maybe_unused]] with __attribute__((unused)) for C compatibility
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            if filename.endswith(('.c', '.h')):
                path = os.path.join(root, filename)
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()
                
                # Update the previous patch to use a C-compatible attribute
                updated = content.replace('[[maybe_unused]]', '__attribute__((unused))')
                
                if updated != content:
                    with open(path, 'w') as f:
                        f.write(updated)

if __name__ == "__main__":
    prepare_source()
