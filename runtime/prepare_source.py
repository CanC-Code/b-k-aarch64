import os
import shutil

def prepare_source():
    print("--- Syncing & Patching Source ---")
    
    # Target the directory containing all C++ source
    base_path = "Android/app/src/main/cpp"
    
    # [span_3](start_span)N64 headers that conflict with Android/Linux system headers[span_3](end_span)
    renames = {
        "string.h": "game_string.h",
        "time.h": "game_time.h",
        "stdlib.h": "game_stdlib.h",
        "sched.h": "game_sched.h"
    }

    # [span_4](start_span)[span_5](start_span)Macro fix for Android Bionic compatibility[span_4](end_span)[span_5](end_span)
    android_macro_fix = """
#ifdef __ANDROID__
  #include <strings.h>
  #undef bcopy
  #undef bzero
  #undef bcmp
#endif
"""

    # [span_6](start_span)Essential N64 type definitions to prevent "unknown type name" errors in NDK[span_6](end_span)
    type_definitions_fix = """
#ifndef _ULTRATYPES_H_FIX_
#define _ULTRATYPES_H_FIX_
typedef signed char            s8;
typedef unsigned char          u8;
typedef signed short           s16;
typedef unsigned short         u16;
typedef signed int             s32;
typedef unsigned int           u32;
typedef signed long long       s64;
typedef unsigned long long     u64;
typedef float                  f32;
typedef double                 f64;
#endif
"""

    bridge_files = ["stubs.cpp", "resource_mgr.cpp", "NativeBridge.cpp", "otr_builder.cpp"]

    # PHASE 1: RECURSIVE RENAME
    # [span_7](start_span)Physical rename of conflicting header files[span_7](end_span)
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if filename in renames:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, renames[filename])
                
                if os.path.exists(new_path):
                    os.remove(new_path)
                shutil.move(old_path, new_path)
                print(f"  [→] Renamed File: {filename} to {renames[filename]}")

    # PHASE 2: RECURSIVE CONTENT PATCH
    # [span_8](start_span)[span_9](start_span)Updates #include lines and injects Android-specific macro fixes[span_8](end_span)[span_9](end_span)
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if filename.endswith(('.c', '.cpp', '.h', '.hpp')):
                file_path = os.path.join(root, filename)
                
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()
                
                original_content = content

                # [span_10](start_span)Replace header references to renamed files[span_10](end_span)
                for old_h, new_h in renames.items():
                    content = content.replace(f'#include <{old_h}>', f'#include <{new_h}>')
                    content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

                # [span_11](start_span)Inject Android fix for specific bridge files[span_11](end_span)
                if filename in bridge_files and "#ifdef __ANDROID__" not in content:
                    content = android_macro_fix + content

                # PHASE 3: TYPE DEFINITION INJECTION
                # [span_12](start_span)Inject basic N64 types into the main SDK header to resolve compilation errors[span_12](end_span)
                if filename == "ultra64.h" and "_ULTRATYPES_H_FIX_" not in content:
                    content = type_definitions_fix + content

                if content != original_content:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"  [✓] Patched Content: {filename}")

if __name__ == "__main__":
    prepare_source()
