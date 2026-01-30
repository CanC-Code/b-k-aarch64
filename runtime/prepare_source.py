import os
import shutil
import re

def prepare_source():
    print("--- Syncing, Patching & Harmonizing Source ---")
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"
    sync_map = {"include": "include", "src": "src"}

    # --- STEP 1: SYNC ---
    for src_sub, dest_sub in sync_map.items():
        full_src = os.path.join(src_root, src_sub)
        full_dest = os.path.join(android_cpp_path, dest_sub)
        if os.path.exists(full_src):
            if os.path.exists(full_dest): shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)
            print(f"  [✓] Synced {src_sub}")

    # --- STEP 2: RENAME SYSTEM HEADERS ---
    renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
    for root, _, files in os.walk(android_cpp_path):
        for filename in files:
            if filename in renames:
                shutil.move(os.path.join(root, filename), os.path.join(root, renames[filename]))

    # --- STEP 3: ADVANCED HARMONIZER ---
    for root, _, files in os.walk(android_cpp_path):
        for filename in files:
            path = os.path.join(root, filename)
            if filename.endswith(('.c', '.cpp', '.h')):
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()

                orig_content = content

                # A. Update includes (Flatten legacy paths and handle renames)
                for old_h, new_h in renames.items():
                    content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')
                    content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')
                
                # Fix legacy path references like "2.0L/PR/sched.h" -> "game_sched.h"
                content = re.sub(r'#include\s+["<](?:2\.0L/PR/)?sched\.h[">]', '#include "game_sched.h"', content)
                content = re.sub(r'#include\s+["<](?:2\.0L/PR/)?string\.h[">]', '#include "game_string.h"', content)

                # B. Leafboat Fix + Memcpy Header Check
                if 'memcpy(' in content or '=' in content:
                    if 'memcpy' in re.findall(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);', content):
                        if "#include <string.h>" not in content and "#include \"game_string.h\"" not in content:
                            content = "#include \"game_string.h\"\n" + content
                    
                    content = re.sub(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);', 
                                     r'\1 \2[\3]; memcpy(\2, \4, \3); // [PATCHED]', content)

                # C. Advanced Type & Linkage Harmonizer (For .c files)
                if filename.endswith('.c'):
                    # Extract Enums and Structs
                    type_defs = re.findall(r'((?:typedef\s+)?(?:struct|enum)\s*([\w\d_]*)\s*\{[^}]+\}\s*([\w\d_]*)\s*;)', content, re.DOTALL)
                    static_defs = re.findall(r'^(static\s+[\w\*]+\s+([\w\d_]+)\s*\([^)]*\))\s*\{', content, re.MULTILINE)

                    if type_defs or static_defs:
                        header_block = "\n// [PATCHED TYPE & FUNCTION BLOCK]\n"
                        for full_type, name1, name2 in type_defs:
                            t_name = name1 if name1 else name2
                            safe_type = f"#ifndef _TYPE_{t_name}\n#define _TYPE_{t_name}\n{full_type}\n#endif\n"
                            header_block += safe_type
                            content = content.replace(full_type, f"// [MOVED TO TOP: {t_name}]\n")
                        
                        for full_sig, func_name in static_defs:
                            header_block += f"{full_sig};\n"
                            ptrn = r'^(?!(?:static|inline|#))([\w\*]+\s+' + re.escape(func_name) + r'\s*\([^;]*\);)'
                            content = re.sub(ptrn, r'static \1', content, flags=re.MULTILINE)

                        include_matches = list(re.finditer(r'#include.*?\n', content))
                        if include_matches:
                            insert_pos = include_matches[-1].end()
                            content = content[:insert_pos] + header_block + content[insert_pos:]
                        else:
                            content = header_block + content

                if content != orig_content:
                    with open(path, 'w') as f: f.write(content)
                    print(f"  [✓] Patched {filename}")

    print("--- Source Preparation Complete ---")

if __name__ == "__main__":
    prepare_source()
