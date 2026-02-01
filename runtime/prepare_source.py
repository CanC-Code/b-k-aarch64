import os
import shutil
import re

class SourceHarmonizerV9_0:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")
        self.existing_types = set()
        self.func_signatures = {}
        self.types_to_forward_declare = set()

    def sync_files(self):
        print("  [>] Pass 0: Intelligent Sync...")
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
                    dest_path = os.path.join(dest_dir, f)
                    if not os.path.exists(dest_path):
                        shutil.copy2(os.path.join(root, f), dest_path)

    def parse_definitions(self):
        """Pass 1: Build a massive exclusion list of every defined type"""
        print("  [>] Pass 1: Recursive Type Discovery...")
        
        # Hard-blacklist primitives and common POSIX types
        self.existing_types.update([
            's8', 'u8', 's16', 'u16', 's32', 'u32', 's64', 'u64', 'f32', 'f64',
            'bool', 'size_t', 'ssize_t', 'off_t', 'uintptr_t', 'intptr_t', 'void',
            'int', 'float', 'char', 'double', 'short', 'long', 'unsigned', 'signed'
        ])
        
        patterns = [
            re.compile(r'typedef\s+(?:struct|union|enum)?\s*[\w\s\*]+\s+([a-zA-Z_]\w*)\s*;'),
            re.compile(r'}\s*([a-zA-Z_]\w*)\s*;'),
            re.compile(r'(?:struct|union|enum)\s+([a-zA-Z_]\w*)\s*\{')
        ]

        # Scan project headers
        for root, _, files in os.walk(self.include_target):
            for f in files:
                if f.endswith('.h'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for pat in patterns:
                            self.existing_types.update(pat.findall(content))
        
        print(f"    Indexed {len(self.existing_types)} protected types.")

    def map_linkage(self):
        """Pass 2: Map signatures and catch truly external types"""
        print("  [>] Pass 2: Linkage Mapping...")
        # Only match function definitions at the start of a line
        func_pat = re.compile(r'^(?:static\s+)?([\w\*]+\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        # Identify types used as pointers
        ptr_type_pat = re.compile(r'\b([a-zA-Z_]\w*)\s*\*')
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for full_sig, name, params in func_pat.findall(content):
                            # Sanitize signature
                            clean_sig = " ".join(full_sig.replace('static ', '').split())
                            self.func_signatures[name] = clean_sig
                            
                            # Check parameters for types we haven't seen defined
                            for t_name in ptr_type_pat.findall(params):
                                if t_name not in self.existing_types and not t_name.endswith('_t'):
                                    self.types_to_forward_declare.add(t_name)

    def promote_linkage(self):
        """Pass 3: Refined static stripping and header injection"""
        print("  [>] Pass 3: Global Linkage Promotion...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        lines = file.readlines()
                    
                    output = []
                    injected = False
                    for line in lines:
                        # ONLY strip static if it is the very first thing on the line (Global)
                        # This avoids breaking local static variables inside functions
                        processed = re.sub(r'^static\s+', '', line)
                        
                        # Inject AFTER the first system include to ensure base types are ready
                        if not injected and '#include' in line:
                            output.append(processed)
                            output.append('#include "harmonized_globals.h"\n')
                            injected = True
                        else:
                            output.append(processed)
                    
                    if not injected:
                        output.insert(0, '#include "harmonized_globals.h"\n')
                        
                    with open(path, 'w') as file:
                        file.writelines(output)

    def generate_header(self):
        """Pass 4: Generate the Master Harmonized Header"""
        print("  [>] Pass 4: Generating Platinum Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            f.write("#include <stdint.h>\n#include <stdbool.h>\n#include <stddef.h>\n\n")
            
            if self.types_to_forward_declare:
                f.write("/* Forward declarations for opaque types */\n")
                for t in sorted(self.types_to_forward_declare):
                    # We use struct forward declaration only; safer against typedef collisions
                    f.write(f"struct {t};\n")
                f.write("\n")
            
            f.write("/* Globally Promoted Functions with Weak Linkage */\n")
            for name, sig in sorted(self.func_signatures.items()):
                f.write(f"__attribute__((weak)) extern {sig};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v9.0 Platinum Ultimate ---\n"
            "include_directories(include)\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C -DFCOMMON)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fcommon -w -O3 -fno-strict-aliasing\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--allow-multiple-definition\")\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# ----------------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files()
        self.parse_definitions()
        self.map_linkage()
        self.promote_linkage()
        self.generate_header()
        self.patch_cmake()
        print("--- v9.0 Platinum Ultimate: Ready ---")

if __name__ == "__main__":
    h = SourceHarmonizerV9_0("Android/app/src/main/cpp", "decomp-files")
    h.run()
