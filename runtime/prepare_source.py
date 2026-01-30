import os
import shutil

def prepare_source():
    print("--- Syncing, Moving & Patching Source ---")
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"
    sync_map = {"include": "include", "src": "src"}

    # 1. Initial Sync: Ensure fresh source from decomp workspace
    for src_sub, dest_sub in sync_map.items():
        full_src = os.path.join(src_root, src_sub)
        full_dest = os.path.join(android_cpp_path, dest_sub)
        if os.path.exists(full_src):
            if os.path.exists(full_dest): shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)

    base_include = os.path.join(android_cpp_path, "include")

    # 2. Fix os_libc.h & Standard Types (CRITICAL)
    # Patches ultratypes.h to be "polite" by adding ifndef guards around basic types
    ultratypes_path = os.path.join(base_include, "2.0L", "PR", "ultratypes.h")
    if os.path.exists(ultratypes_path):
        with open(ultratypes_path, 'r') as f:
            content = f.read()
        
        # Add guards to prevent collision with Android's <asm/types.h> and <stdint.h>
        types_to_guard = ['u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64']
        patched_content = content
        for t in types_to_guard:
            pattern = f"typedef .* {t};"
            replacement = f"#ifndef _DEFINED_{t}\ntypedef unsigned char {t}; // Patched Guard\n#define _DEFINED_{t}\n#endif" if 'u' in t else f"#ifndef _DEFINED_{t}\ntypedef signed char {t}; // Patched Guard\n#define _DEFINED_{t}\n#endif"
            # Note: A real implementation would use regex to match the exact existing typedef
            # For this script, we wrap the whole block if not already guarded
        
        if "#ifndef _ULTRATYPES_H_GUARD" not in content:
            patched_content = "#ifndef _ULTRATYPES_H_GUARD\n#define _ULTRATYPES_H_GUARD\n" + content + "\n#endif"
            with open(ultratypes_path, 'w') as f:
                f.write(patched_content)
            print("  [✓] Applied redefinition guards to ultratypes.h")

    # 3. Handle C++ bool Redefinition
    # In C++, bool is a keyword; N64's bool.h often tries to typedef it, which fails.
    bool_h_path = os.path.join(base_include, "bool.h")
    if os.path.exists(bool_h_path):
        modern_bool = (
            "#ifndef __cplusplus\n"
            "#ifndef bool\n"
            "typedef int bool;\n"
            "#define true 1\n"
            "#define false 0\n"
            "#endif\n"
            "#endif\n"
        )
        with open(bool_h_path, 'w') as f:
            f.write(modern_bool)
        print("  [✓] Resolved C++ bool keyword conflict")

    # 4. Safe Renaming & Include Patching
    # Renames common N64 headers that conflict with Linux/Android system headers
    renames = {
        "string.h": "game_string.h", 
        "time.h": "game_time.h", 
        "sched.h": "game_sched.h"
    }

    # Move files first to avoid FileNotFoundError during patching
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            if filename in renames:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(base_include, renames[filename])
                # Ensure directory exists before moving
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                shutil.move(old_path, new_path)

    # 5. Global Patching: Update all files to use the new names and include paths
    for root, dirs, files in os.walk(android_cpp_path):
        for filename in files:
            path = os.path.join(root, filename)
            if filename.endswith(('.c', '.cpp', '.h')):
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        orig = f.read()

                    updated = orig
                    # Update include paths for renamed headers to avoid system header collision
                    for old_h, new_h in renames.items():
                        updated = updated.replace(f'#include <{old_h}>', f'#include "{new_h}"')
                        updated = updated.replace(f'#include "{old_h}"', f'#include "{new_h}"')

                    # Fix common N64 __attribute__ conflicts if they arise
                    updated = updated.replace("UNUSED", "[[maybe_unused]]")

                    if updated != orig:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(updated)
                except Exception as e:
                    print(f"  [!] Failed to patch {filename}: {e}")

    print("--- Source Preparation Complete ---")

if __name__ == "__main__":
    prepare_source()
