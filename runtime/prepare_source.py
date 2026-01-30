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

    # --- STEP 2: PATCH os_libc.h ---
    os_libc_path = os.path.join(base_include, "2.0L", "PR", "os_libc.h")
    if os.path.exists(os_libc_path):
        with open(os_libc_path, 'r') as f:
            content = f.read()
        if 'extern "C"' not in content:
            patched = f"#ifndef _OS_LIBC_PATCH_H\n#define _OS_LIBC_PATCH_H\n#include <string.h>\n#include <strings.h>\n#undef bcopy\n#undef bzero\n#undef bcmp\n#ifdef __cplusplus\nextern \"C\" {{\n#endif\n{content}\n#ifdef __cplusplus\n}}\n#endif\n#endif"
            with open(os_libc_path, 'w') as f: f.write(patched)
            print("  [✓] Patched os_libc.h")

    # --- STEP 3: FIX bool.h ---
    bool_h_path = os.path.join(base_include, "bool.h")
    if os.path.exists(bool_h_path):
        with open(bool_h_path, 'w') as f:
            f.write("#ifndef __cplusplus\ntypedef int bool;\n#define true 1\n#define false 0\n#endif\n")
        print("  [✓] Patched bool.h")

    # --- STEP 4: RENAME SYSTEM HEADERS ---
    renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
    for root, _, files in os.walk(android_cpp_path):
        for filename in files:
            if filename in renames:
                shutil.move(os.path.join(root, filename), os.path.join(root, renames[filename]))

    # --- STEP 5 & 6: ADVANCED SOURCE HARMONIZER ---
    for root, _, files in os.walk(android_cpp_path):
        for filename in files:
            path = os.path.join(root, filename)
            if filename.endswith(('.c', '.cpp', '.h')):
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()

                orig_content = content

                # A. Update includes
                for old_h, new_h in renames.items():
                    content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')
                    content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

                # B. Leafboat Fix
                content = re.sub(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);', 
                                 r'\1 \2[\3]; memcpy(\2, \4, \3); // [PATCHED]', content)

                # C. Advanced Type & Linkage Harmonizer
                if filename.endswith('.c'):
                    # 1. Extract Enums and Structs to prevent "incomplete type" errors
                    # This finds 'typedef struct { ... } name;' or 'enum name { ... };'
                    type_defs = re.findall(r'((?:typedef\s+)?(?:struct|enum)\s*[\w\d_]*\s*\{[^}]+\}\s*[\w\d_]*\s*;)', content, re.DOTALL)
                    for td in type_defs:
                        content = content.replace(td, "") # Remove from original location
                    
                    # 2. Extract Static Function Signatures
                    static_defs = re.findall(r'^(static\s+[\w\*]+\s+([\w\d_]+)\s*\([^)]*\))\s*\{', content, re.MULTILINE)
                    declarations = [f"{sig};" for sig, name in static_defs]

                    # 3. Clean existing problematic forward declarations
                    for _, name in static_defs:
                        content = re.sub(r'^(static\s+)?[\w\*]+\s+' + re.escape(name) + r'\s*\([^;]*\);', "", content, flags=re.MULTILINE)

                    # 4. Reconstruct the Header Block
                    header_block = "\n// [AUTO-GENERATED COMPATIBILITY BLOCK]\n"
                    header_block += "\n".join(type_defs) + "\n"
                    header_block += "\n".join(declarations) + "\n"

                    # 5. Inject after the last include
                    if "#include" in content:
                        content = re.sub(r'(.*#include.*?\n)(?!#include)', r'\1' + header_block, content, count=1, flags=re.DOTALL)
                    else:
                        content = header_block + content

                if content != orig_content:
                    with open(path, 'w') as f: f.write(content)
                    print(f"  [✓] Harmonized {filename}")

    print("--- Source Preparation Complete ---")

if __name__ == "__main__":
    prepare_source()
