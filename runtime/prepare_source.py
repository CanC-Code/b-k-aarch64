import os

# Files to inject the Android fix into
BRIDGE_FILES = [
    "Android/app/src/main/cpp/emulator/stubs.cpp",
    "Android/app/src/main/cpp/emulator/resource_mgr.cpp",
    "Android/app/src/main/cpp/ultra/NativeBridge.cpp",
    "Android/app/src/main/cpp/ultra/otr_builder.cpp"
]

# The fix to prevent Android's strings.h from breaking legacy bcopy/bzero
ANDROID_MACRO_FIX = """
#ifdef __ANDROID__
  #include <strings.h>
  #undef bcopy
  #undef bzero
#endif
"""

def prepare_source():
    print("--- Syncing & Patching Source ---")
    
    # 1. Rename files to avoid system collision
    # Ensure stdlib.h is also handled since your log missed it
    renames = {
        "string.h": "game_string.h",
        "time.h": "game_time.h",
        "stdlib.h": "game_stdlib.h",
        "sched.h": "game_sched.h"
    }

    # 2. Walk through all files to apply renaming and injections
    base_path = "Android/app/src/main/cpp"
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            
            # Read file content
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read()

            # Apply replacements for renamed headers
            original_content = content
            for old, new in renames.items():
                content = content.replace(f'#include <{old}>', f'#include <{new}>')
                content = content.replace(f'#include "{old}"', f'#include "{new}"')

            # Inject Android Macro Fix if it's one of our bridge files
            if file_path.replace("\\", "/") in [f.replace("\\", "/") for f in BRIDGE_FILES]:
                if "#ifdef __ANDROID__" not in content:
                    content = ANDROID_MACRO_FIX + content
            
            # Write back if changed
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"  [✓] Patched: {filename}")

    # Physical rename of files (run after patching references)
    for old_name, new_name in renames.items():
        # You'll need to locate these in your specific include dirs
        # Example for the 2.0L/PR directory
        target = f"Android/app/src/main/cpp/include/2.0L/PR/{old_name}"
        if os.path.exists(target):
            os.rename(target, target.replace(old_name, new_name))
            print(f"  [→] Renamed: {old_name} to {new_name}")

if __name__ == "__main__":
    prepare_source()
