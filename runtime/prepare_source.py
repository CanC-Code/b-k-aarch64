import os
import shutil
import re

def prepare_source():
    print("--- Syncing & Fixing Legacy C Syntax ---")
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"
    
    # [Existing Sync Logic here...]

    # 1. Fix Legacy Array Initializations (The "Leafboat" Fix)
    # This finds 'u8 arr[N] = SYMBOL;' and converts it to 'u8 arr[N]; memcpy(arr, SYMBOL, N);'
    for root, _, files in os.walk(os.path.join(android_cpp_path, "src")):
        for filename in files:
            if filename.endswith('.c'):
                path = os.path.join(root, filename)
                with open(path, 'r') as f:
                    lines = f.readlines()
                
                new_lines = []
                changed = False
                for line in lines:
                    # Regex to find: type name[size] = symbol;
                    match = re.search(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);', line)
                    if match:
                        v_type, v_name, v_size, v_val = match.groups()
                        # Replace with declaration + memcpy
                        new_line = f"    {v_type} {v_name}[{v_size}]; memcpy({v_name}, {v_val}, {v_size}); // [PATCHED LEGACY INIT]\n"
                        new_lines.append(new_line)
                        changed = True
                    else:
                        new_lines.append(line)
                
                if changed:
                    with open(path, 'w') as f:
                        f.writelines(new_lines)
                    print(f"  [✓] Patched legacy array init in {filename}")

    # 2. Add 'string.h' to global PCH if not already there
    # This ensures memcpy is always available for the fix above
    # [Refer to previous CMakeLists.txt updates]

if __name__ == "__main__":
    prepare_source()
