import os
import shutil
import re

def prepare_source():
    print("--- Syncing, Patching & Fixing Legacy Syntax ---")
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"
    sync_map = {"include": "include", "src": "src"}

    # --- STEP 1: SYNC FILES ---
    # Moves files from the decompilation root to the Android project structure
    for src_sub, dest_sub in sync_map.items():
        full_src = os.path.join(src_root, src_sub)
        full_dest = os.path.join(android_cpp_path, dest_sub)
        if os.path.exists(full_src):
            if os.path.exists(full_dest): shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)
            print(f"  [✓] Synced {src_sub}")

    base_include = os.path.join(android_cpp_path, "include")

    # --- STEP 2: PATCH os_libc.h (Fix Linkage & Macro Conflicts) ---
    # Adds extern "C" wrappers and undefines macros that conflict with modern NDK headers
    os_libc_path = os.path.join(base_include, "2.0L", "PR", "os_libc.h")
    if os.path.exists(os_libc_path):
        with open(os_libc_path, 'r') as f:
            content = f.read()
        if 'extern "C"' not in content:
            patched = (
                "#ifndef _OS_LIBC_PATCH_H\n"
                "#define _OS_LIBC_PATCH_H\n"
                "#include <string.h>\n" 
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
    # Prevents Clang from picking game-specific headers over standard library headers
    renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}

    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            if filename in renames:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(os.path.dirname(old_path), renames[filename])
                shutil.move(old_path, new_path)
                print(f"  [✓] Renamed {filename} to {renames[filename]}")

    # --- STEP 5 & 6: PATCH CONTENT & HARMONIZE STATIC DECLARATIONS ---
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            path = os.path.join(root, filename)
            if filename.endswith(('.c', '.cpp', '.h')):
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()
                
                orig_content = content

                # A. Update includes for renamed files
                for old_h, new_h in renames.items():
                    content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')
                    content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

                # B. Leafboat Fix (Legacy Array Initialization)
                # Converts 'u8 arr[N] = SYMBOL;' to 'u8 arr[N]; memcpy(arr, SYMBOL, N);'
                content = re.sub(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);', 
                                 r'\1 \2[\3]; memcpy(\2, \4, \3); // [PATCHED]', content)

                # C. Harmonize Static Declarations
                # Fixes "static declaration follows non-static declaration" errors in code_BF0.c, etc.
                # 1. Find functions implemented as static
                static_funcs = re.findall(r'^static\s+[\w\*]+\s+([\w\d_]+)\s*\(', content, re.MULTILINE)
                for func_name in static_funcs:
                    # 2. Find and fix their non-static forward declarations
                    ptrn = r'^(?!(?:static|inline|#))([\w\*]+\s+' + re.escape(func_name) + r'\s*\([^;]*\);)'
                    content = re.sub(ptrn, r'static \1', content, flags=re.MULTILINE)

                # D. Ensure renamed headers include base types
                if filename in renames.values() and 'ultratypes.h' not in content:
                    content = '#include "2.0L/PR/ultratypes.h"\n' + content

                if content != orig_content:
                    with open(path, 'w') as f:
                        f.write(content)
                    if "static" in content and "static" not in orig_content:
                        print(f"  [✓] Harmonized static declarations in {filename}")

    print("--- Source Preparation Complete ---")

if __name__ == "__main__":
    prepare_source()
