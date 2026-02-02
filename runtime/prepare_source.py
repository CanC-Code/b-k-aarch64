import os
import shutil
import re

class SourceHarmonizerV9_6:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")
        self.func_signatures = {}
        self.opaque_types = set()
        self.protected_types = {
            'void', 'char', 'int', 'long', 'float', 'double', 'short', 'signed', 'unsigned',
            'u8', 's8', 'u16', 's16', 'u32', 's32', 'u64', 's64', 'f32', 'f64',
            'Vtx', 'Mtx', 'Gfx', 'u_long', 'u_short', 'u_int', 'u_char', 'bool',
            'size_t', 'uintptr_t', 'intptr_t', 'LookAt', 'Hilite'
        }

    def sync_files(self):
        print("  [>] Pass 0: Syncing...")
        for sub in ["src", "include"]:
            source = os.path.join(self.decomp_path, sub)
            target = os.path.join(self.android_path, sub)
            if not os.path.exists(source): continue
            os.makedirs(target, exist_ok=True)
            for root, _, files in os.walk(source):
                rel = os.path.relpath(root, source)
                dest_dir = os.path.join(target, rel)
                os.makedirs(dest_dir, exist_ok=True)
                for f in files:
                    shutil.copy2(os.path.join(root, f), os.path.join(dest_dir, f))

    def map_linkage(self):
        print("  [>] Pass 1: Final Linkage Mapping...")
        # Catch function definitions
        func_pat = re.compile(r'^(?:static\s+)?([\w\*]+\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        # Deep pointer discovery for every word before a '*'
        ptr_find = re.compile(r'\b([a-zA-Z_]\w*)\s*(?=\*)')
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for full_sig, name, params in func_pat.findall(content):
                            # Normalize whitespace
                            sig = " ".join(full_sig.replace('static ', '').split())
                            
                            # Extract and tag unknown types
                            for t in ptr_find.findall(sig):
                                if t not in self.protected_types and not t.endswith('_t'):
                                    self.opaque_types.add(t)
                                    # Regex replace only if not already prefixed by 'struct'
                                    sig = re.sub(fr'(?<!struct\s)\b{t}\b', f'struct {t}', sig)
                            
                            self.func_signatures[name] = sig

    def promote_linkage(self):
        print("  [>] Pass 2: Globalization...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        lines = file.readlines()
                    
                    output = []
                    for line in lines:
                        # Strip static from global scope
                        processed = re.sub(r'^static\s+', '', line)
                        output.append(processed)
                    
                    # Essential: The harmonized header MUST be at the end to avoid 
                    # conflicting with internal headers that have better info
                    output.append('\n#include "harmonized_globals.h"\n')
                        
                    with open(path, 'w') as file:
                        file.writelines(output)

    def generate_header(self):
        print("  [>] Pass 3: Generating Final Ultimate Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            f.write("#include <ultra64.h>\n#include <stdint.h>\n#include <stddef.h>\n#include <stdbool.h>\n\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            f.write("/* Opaque Tag Forwarding */\n")
            for t in sorted(self.opaque_types):
                # Use a tag-based approach that works even if the user later typedefs it
                f.write(f"struct {t};\n")
            
            f.write("\n/* Weak Symbols for Linker Resolution */\n")
            for name, sig in sorted(self.func_signatures.items()):
                # Weak attribute ensures this is only used if no other definition exists
                f.write(f"__attribute__((weak)) extern {sig};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v9.6 Final Ultimate ---\n"
            "include_directories(include)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fcommon -w -O3 -fno-strict-aliasing -fpermissive\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--allow-multiple-definition\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C -DFCOMMON)\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# --------------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files()
        self.map_linkage()
        self.promote_linkage()
        self.generate_header()
        self.patch_cmake()
        print("--- v9.6 Final Ultimate: Build Ready ---")

if __name__ == "__main__":
    h = SourceHarmonizerV9_6("Android/app/src/main/cpp", "decomp-files")
    h.run()
