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

    # --- STEP 4: RENAME SYSTEM HEADERS ---
    renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
    for root, _, files in os.walk(android_cpp_path):
        for filename in files:
            if filename in renames:
                shutil.move(os.path.join(root, filename), os.path.join(root, renames[filename]))

    # --- STEP 5 & 6: SAFE SOURCE HARMONIZER ---
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

                # B. Leafboat Fix (Legacy Array Initialization)
                content = re.sub(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);', 
                                 r'\1 \2[\3]; memcpy(\2, \4, \3); // [PATCHED]', content)

                # C. Safe Harmonizer: Inject declarations WITHOUT moving original code
                if filename.endswith('.c'):
                    # 1. Identify all static function definitions
                    # Matches: static [type] [name]([args]) {
                    static_defs = re.findall(r'^(static\s+[\w\*]+\s+([\w\d_]+)\s*\([^)]*\))\s*\{', content, re.MULTILINE)
                    
                    if static_defs:
                        declarations = []
                        for full_sig, func_name in static_defs:
                            declarations.append(f"{full_sig};")
                            # Fix existing non-static declarations that might conflict
                            ptrn = r'^(?!(?:static|inline|#))([\w\*]+\s+' + re.escape(func_name) + r'\s*\([^;]*\);)'
                            content = re.sub(ptrn, r'static \1', content, flags=re.MULTILINE)
                        
                        header_block = "\n// [SAFE FORWARD DECLARATIONS]\n" + "\n".join(declarations) + "\n"
                        
                        # 2. Find the best injection point (after last include)
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
