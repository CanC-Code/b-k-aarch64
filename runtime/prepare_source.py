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

                # B. Fix memory copies
                content = re.sub(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);', 
                                 r'\1 \2[\3]; memcpy(\2, \4, \3); // [PATCHED]', content)

                # C. Linkage & Guarded Type Harmonizer
                if filename.endswith('.c'):
                    # Match structs/enums: capturing the name for the guard
                    # This regex looks for: typedef (opt) struct/enum NAME { ... } NAME (opt);
                    type_pattern = r'((?:typedef\s+)?(?:struct|enum)\s*([\w\d_]*)\s*\{[^}]+\}\s*([\w\d_]*)\s*;)'
                    type_matches = re.findall(type_pattern, content, re.DOTALL)
                    
                    static_funcs = re.findall(r'^static\s+[\w\*]+\s+([\w\d_]+)\s*\(', content, re.MULTILINE)
                    
                    if type_matches or static_funcs:
                        header_block = "\n// [PATCHED TYPE & PROTOTYPE BLOCK]\n"
                        
                        for full_def, name1, name2 in type_matches:
                            # Use name1 (struct name) or name2 (typedef name) for the guard
                            t_name = name1 if name1 else name2
                            if t_name:
                                guarded_type = f"#ifndef _GUARD_{t_name}\n#define _GUARD_{t_name}\n{full_def}\n#endif\n"
                                header_block += guarded_type
                                content = content.replace(full_def, f"// [MOVED: {t_name}]\n")
                        
                        for func_name in static_funcs:
                            sig_match = re.search(r'^(static\s+[\w\*]+\s+' + re.escape(func_name) + r'\s*\([^)]*\))', content, re.MULTILINE)
                            if sig_match:
                                header_block += f"{sig_match.group(1)};\n"
                            # Fix non-static forward declarations
                            ptrn = r'^([\w\*]+\s+' + re.escape(func_name) + r'\s*\([^;]*\);)'
                            content = re.sub(ptrn, r'static \1', content, flags=re.MULTILINE)

                        include_matches = list(re.finditer(r'#include.*?\n', content))
                        if include_matches:
                            insert_pos = include_matches[-1].end()
                            content = content[:insert_pos] + header_block + content[insert_pos:]
                        else:
                            content = header_block + content

                # D. Fix Core Engine specific missing identifiers (code_1D00.c)
                if filename == "code_1D00.c":
                    content = content.replace('extern void n_alInit(N_ALGlobals *, ALSynConfig *);', 
                                            '// [PATCHED] alInit')
                    
                    if 'audioManager' in content and 'extern struct' not in content:
                        injection = (
                            "\n#ifndef _AM_GUARD\n#define _AM_GUARD\n"
                            "extern struct { \n    OSMesgQueue audioReplyMsgQ; \n    OSMesg audioReplyMsgBuf[8]; \n"
                            "    OSMesgQueue audioFrameMsgQ; \n    OSMesg audioFrameMsgBuf[8]; \n"
                            "    void* ACMDList[3]; \n    struct audioInfo* audioInfo[3]; \n"
                            "    OSThread thread; \n} audioManager;\n"
                            "#endif\n"
                        )
                        if 'D_8027D5B0' in content:
                            injection += "extern struct { int unk4; int unk8; } D_8027D5B0;\n"
                        
                        content = content.replace("#include \"game_sched.h\"", "#include \"game_sched.h\"\n" + injection)

                if content != orig_content:
                    with open(path, 'w') as f: f.write(content)
                    print(f"  [✓] Patched {filename}")

    print("--- Source Preparation Complete ---")

if __name__ == "__main__":
    prepare_source()
