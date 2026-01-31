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

                # A. Update includes & Flatten legacy paths
                for old_h, new_h in renames.items():
                    content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')
                    content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')
                
                content = re.sub(r'#include\s+["<](?:2\.0L/PR/)?sched\.h[">]', '#include "game_sched.h"', content)
                content = re.sub(r'#include\s+["<](?:2\.0L/PR/)?string\.h[">]', '#include "game_string.h"', content)

                # B. Fix memory copies and legacy assignments
                content = re.sub(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);', 
                                 r'\1 \2[\3]; memcpy(\2, \4, \3); // [PATCHED]', content)

                # C. Advanced Type & Linkage Harmonizer
                if filename.endswith('.c'):
                    # Fix n_alInit declaration conflict found in log
                    content = content.replace('extern void n_alInit(N_ALGlobals *, ALSynConfig *);', 
                                            '// [PATCHED] extern void n_alInit(N_ALGlobals *, ALSynConfig *);')

                # D. Fix Core Engine specific missing identifiers (code_1D00.c)
                if filename == "code_1D00.c":
                    injection = "\n// [PATCHED] Global declarations for missing core identifiers\n"
                    
                    # Inject audioManager global structure
                    if 'audioManager' in content and 'struct' not in content:
                        injection += "extern struct { \n    OSMesgQueue audioReplyMsgQ; \n    OSMesg audioReplyMsgBuf[8]; \n"
                        injection += "    OSMesgQueue audioFrameMsgQ; \n    OSMesg audioFrameMsgBuf[8]; \n"
                        injection += "    void* ACMDList[3]; \n    struct audioInfo* audioInfo[3]; \n"
                        injection += "    OSThread thread; \n} audioManager;\n"
                    
                    # Inject D_8027D5B0 global structure
                    if 'D_8027D5B0' in content:
                        injection += "extern struct { int unk4; int unk8; } D_8027D5B0;\n"
                        
                    include_matches = list(re.finditer(r'#include.*?\n', content))
                    if include_matches:
                        insert_pos = include_matches[-1].end()
                        content = content[:insert_pos] + injection + content[insert_pos:]

                if content != orig_content:
                    with open(path, 'w') as f: f.write(content)
                    print(f"  [✓] Patched {filename}")

    print("--- Source Preparation Complete ---")

if __name__ == "__main__":
    prepare_source()
