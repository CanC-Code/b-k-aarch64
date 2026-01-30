import os
import shutil
import re

def prepare_source():
    print("--- Syncing & Patching Source for Android Compatibility ---")
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"
    sync_map = {"include": "include", "src": "src"}

    # 1. Sync files
    for src_sub, dest_sub in sync_map.items():
        full_src = os.path.join(src_root, src_sub)
        full_dest = os.path.join(android_cpp_path, dest_sub)
        if os.path.exists(full_src):
            if os.path.exists(full_dest): shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)

    base_include = os.path.join(android_cpp_path, "include")

    # 2. Files and functions that conflict with Android's Bionic libc
    # Added malloc and realloc to this list
    conflict_map = {
        os.path.join(base_include, "game_string.h"): ['strcat', 'strcpy', 'strlen', 'memcpy', 'memmove'],
        os.path.join(base_include, "string.h"):      ['strcat', 'strcpy', 'strlen', 'memcpy', 'memmove'],
        os.path.join(base_include, "functions.h"):   ['malloc', 'realloc', 'free'],
        os.path.join(base_include, "core1", "mem.h"): ['memcpy', 'memmove', 'wmemcpy'],
        os.path.join(base_include, "2.0L", "PR", "os_libc.h"): ['bcmp', 'bzero', 'strlen', 'memcpy']
    }

    for file_path, funcs in conflict_map.items():
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            new_lines = []
            for line in lines:
                should_comment = False
                for func in funcs:
                    # Match function name with a boundary to avoid partial matches
                    if re.search(rf'\b{func}\b', line) and ';' in line:
                        should_comment = True
                        break
                
                if should_comment:
                    new_lines.append("// [PATCH] " + line)
                else:
                    new_lines.append(line)

            with open(file_path, 'w') as f:
                f.writelines(new_lines)
            print(f"  [✓] Patched conflicts in {os.path.basename(file_path)}")

    # 3. Recursive attribute fix (for [[maybe_unused]] issues)
    for root, _, files in os.walk(android_cpp_path):
        for filename in files:
            if filename.endswith(('.c', '.h')):
                path = os.path.join(root, filename)
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()
                
                # Convert modern C++ attributes to C-compatible ones
                updated = content.replace('[[maybe_unused]]', '__attribute__((unused))')
                
                if updated != content:
                    with open(path, 'w') as f:
                        f.write(updated)

if __name__ == "__main__":
    prepare_source()
