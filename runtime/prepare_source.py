import os
import re

def patch_file(file_path, patch_map):
    if not os.path.exists(file_path):
        print(f"Skipping: {file_path} (Not found)")
        return
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    for search, replace in patch_map.items():
        content = content.replace(search, replace)
        
    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Patched: {file_path}")

def main():
    cpp_root = "Android/app/src/main/cpp"
    
    print("--- Applying Android C++ Compatibility Patches ---")

    # 1. Fix os_libc.h linkage globally
    # This prevents 'sprintf' from conflicting with the NDK's C++ signatures
    libc_h = f"{cpp_root}/include/2.0L/PR/os_libc.h"
    patch_file(libc_h, {
        'extern int              sprintf(char *s, const char *fmt, ...);': 
        '#ifdef __cplusplus\nextern "C" {\n#endif\nextern int sprintf(char *s, const char *fmt, ...);\n#ifdef __cplusplus\n}\n#endif'
    })

    # 2. Fix C++ files requiring sched_yield and C linkage
    # These files include C++ headers (like <map> or <string>) which trigger the NDK's stdio.h
    cpp_files = [
        f"{cpp_root}/emulator/stubs.cpp",
        f"{cpp_root}/emulator/resource_mgr.cpp",
        f"{cpp_root}/ultra/NativeBridge.cpp"
    ]

    for c_file in cpp_files:
        if os.path.exists(c_file):
            with open(c_file, 'r') as f:
                lines = f.readlines()
            
            new_content = []
            # Inject sched.h for sched_yield
            new_content.append("#include <sched.h>\n")
            
            in_legacy_block = False
            for line in lines:
                # Wrap legacy includes in extern "C"
                if ("2.0L" in line or "ultratypes.h" in line or "macros.h" in line) and not in_legacy_block:
                    new_content.append('extern "C" {\n')
                    new_content.append(line)
                    in_legacy_block = True
                elif in_legacy_block and "#include" not in line and line.strip() != "":
                    new_content.append('}\n')
                    new_content.append(line)
                    in_legacy_block = False
                else:
                    new_content.append(line)
            
            with open(c_file, 'w') as f:
                f.writelines(new_content)
            print(f"Injected system guards and C-linkage into: {os.path.basename(c_file)}")

    # 3. Handle Shadow Headers (Existing Logic)
    shadow_headers = {
        f"{cpp_root}/include/string.h": f"{cpp_root}/include/game_string.h",
        f"{cpp_root}/include/time.h": f"{cpp_root}/include/game_time.h"
    }

    for src, dst in shadow_headers.items():
        if os.path.exists(src):
            os.rename(src, dst)
            print(f"Renamed shadow header: {os.path.basename(src)} -> {os.path.basename(dst)}")

    # 4. Portability Patches (Existing Logic)
    patch_file(f"{cpp_root}/include/2.0L/PR/ultratypes.h", {
        "typedef unsigned long       u32;": "typedef unsigned int u32;",
        "typedef signed long         s32;": "typedef signed int s32;"
    })

    print("Build directory ready!")

if __name__ == "__main__":
    main()
