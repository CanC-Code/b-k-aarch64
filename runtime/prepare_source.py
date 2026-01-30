import os
import shutil
import re

def prepare_source():
    print("--- Syncing, Patching & Fixing Legacy Syntax ---")
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"
    sync_map = {"include": "include", "src": "src"}

    # --- STEP 1: SYNC FILES ---
    for src_sub, dest_sub in sync_map.items():
        full_src = os.path.join(src_root, src_sub)
        full_dest = os.path.join(android_cpp_path, dest_sub)
        if os.path.exists(full_src):
            if os.path.exists(full_dest): shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)
            print(f"  [✓] Synced {src_sub}")

    base_include = os.path.join(android_cpp_path, "include")
    
    # --- STEP 2: PATCH os_libc.h (Fix Linkage & Conflicts) ---
    os_libc_path = os.path.join(base_include, "2.0L", "PR", "os_libc.h")
    if os.path.exists(os_libc_path):
        with open(os_libc_path, 'r') as f:
            content = f.read()
        if 'extern "C"' not in content:
            patched = (
                "#ifndef _OS_LIBC_PATCH_H\n"
                "#define _OS_LIBC_PATCH_H\n"
                "#include <string.h>\n" # For memcpy
                "#include <strings.h>\n"
                "#undef bcopy\n"
                "#undef bzero\n"
                "#undef bcmp\n"
                "#ifdef __cplusplus\n"
                "extern \"C\" {\n"
                "#endif\n"
                f"{content}\n"
                "#ifdef __cplusplus\n"
                "}\n"
                "#endif\n"
                "#endif"
            )
            with open(os_libc_path, 'w') as f:
                f.write(patched)
            print("  [✓] Patched os_libc.h")

    # --- STEP 3: FIX bool.h (Prevent collision with C++) ---
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
        print("  [✓] Patched bool.h")

    # --- STEP 4: RENAME SYSTEM HEADERS ---
    # This prevents the compiler from confusing game headers with Android system headers
    renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
    
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            if filename in renames:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(os.path.dirname(old_path), renames[filename])
                shutil.move(old_path, new_path)
                print(f"  [✓] Renamed {filename} to {renames[filename]}")

    # --- STEP 5: PATCH CONTENT & LEGACY ARRAY INIT ---
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            path = os.path.join(root, filename)
            if filename.endswith(('.c', '.cpp', '.h')):
                with open(path, 'r', errors='ignore') as f:
                    lines = f.readlines()
                
                new_lines = []
                changed = False
                for line in lines:
                    # A. Update includes for renamed files
                    temp_line = line
                    for old_h, new_h in renames.items():
                        temp_line = temp_line.replace(f'#include <{old_h}>', f'#include "{new_h}"')
                        temp_line = temp_line.replace(f'#include "{old_h}"', f'#include "{new_h}"')
                    
                    # B. Fix Legacy Array Initializations (The "Leafboat" Fix)
                    # Finds: type name[size] = symbol;
                    match = re.search(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);', temp_line)
                    if match and not filename.endswith('.h'): # Don't patch externs in headers
                        v_type, v_name, v_size, v_val = match.groups()
                        temp_line = f"    {v_type} {v_name}[{v_size}]; memcpy({v_name}, {v_val}, {v_size}); // [PATCHED LEGACY INIT]\n"
                        changed = True
                    
                    if temp_line != line:
                        changed = True
                    new_lines.append(temp_line)

                # C. Ensure types are included in renamed headers
                if filename in renames.values() and 'ultratypes.h' not in "".join(new_lines):
                    new_lines.insert(0, '#include "2.0L/PR/ultratypes.h"\n')
                    changed = True

                if changed:
                    with open(path, 'w') as f:
                        f.writelines(new_lines)

    print("--- Source Preparation Complete ---")

if __name__ == "__main__":
    prepare_source()
