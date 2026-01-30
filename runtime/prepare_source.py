import os
import shutil
import re

def prepare_source():
    print("--- Syncing & Advanced Patching for Android ---")
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

    # 2. Fix Struct Visibility in structs.h
    structs_h = os.path.join(base_include, "structs.h")
    if os.path.exists(structs_h):
        with open(structs_h, 'r') as f:
            content = f.read()
        
        # Inject forward declarations at the very top
        forward_decls = (
            "#ifndef STRUCTS_FORWARD_DECLS\n"
            "#define STRUCTS_FORWARD_DECLS\n"
            "struct actor_s;\n"
            "struct actorMarker_s;\n"
            "struct struct_68_s;\n"
            "struct BKModelBin;\n"
            "#endif\n\n"
        )
        if "STRUCTS_FORWARD_DECLS" not in content:
            with open(structs_h, 'w') as f:
                f.write(forward_decls + content)
            print("  [✓] Added forward declarations to structs.h")

    # 3. Patch conflicting LibC functions (Carry over from previous step)
    conflict_map = {
        os.path.join(base_include, "functions.h"):   ['malloc', 'realloc', 'free', 'sprintf'],
        os.path.join(base_include, "string.h"):      ['strcat', 'strcpy', 'strlen', 'memcpy', 'memmove'],
        os.path.join(base_include, "2.0L", "PR", "os_libc.h"): ['bcmp', 'bzero', 'strlen', 'memcpy']
    }

    for file_path, funcs in conflict_map.items():
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()
            new_lines = [("// [PATCH] " + l if any(re.search(rf'\b{fn}\b', l) and ';' in l for fn in funcs) else l) for l in lines]
            with open(file_path, 'w') as f:
                f.writelines(new_lines)

    # 4. Global Attribute and Type fixes
    for root, _, files in os.walk(android_cpp_path):
        for filename in files:
            if filename.endswith(('.c', '.h')):
                path = os.path.join(root, filename)
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()
                # Fix modern attributes for older C standard
                updated = content.replace('[[maybe_unused]]', '__attribute__((unused))')
                if updated != content:
                    with open(path, 'w') as f:
                        f.write(updated)

if __name__ == "__main__":
    prepare_source()
