import os
import shutil
import re

class SourceHarmonizerV8_8:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")
        self.existing_types = set()
        self.func_signatures = {}
        self.types_used_in_signatures = set()

    def sync_files(self):
        print("  [>] Syncing Files...")
        # (Standard sync logic remains the same to preserve Android JNI files)
        for sub in ["src", "include"]:
            source = os.path.join(self.decomp_path, sub)
            target = os.path.join(self.android_path, sub)
            if os.path.exists(source):
                if os.path.exists(target):
                    # Intelligent merge
                    for root, _, files in os.walk(source):
                        rel = os.path.relpath(root, source)
                        dest_dir = os.path.join(target, rel)
                        os.makedirs(dest_dir, exist_ok=True)
                        for f in files:
                            if not os.path.exists(os.path.join(dest_dir, f)):
                                shutil.copy2(os.path.join(root, f), os.path.join(dest_dir, f))
                else:
                    shutil.copytree(source, target)

    def parse_existing_definitions(self):
        """Pass 1: Discover all types defined in the actual project headers"""
        print("  [>] Pass 1: Global Type Discovery...")
        # Blacklist primitives that should never be forward-declared
        self.existing_types.update([
            's8', 'u8', 's16', 'u16', 's32', 'u32', 's64', 'u64', 
            'f32', 'f64', 'bool', 'size_t', 'uintptr_t', 'intptr_t'
        ])
        
        patterns = [
            re.compile(r'typedef\s+(?:struct|union|enum)?\s*[\w\s\*]+\s+([a-zA-Z_]\w*)\s*;'),
            re.compile(r'}\s*([a-zA-Z_]\w*)\s*;'),
            re.compile(r'(?:struct|union|enum)\s+([a-zA-Z_]\w*)\s*\{')
        ]

        if os.path.exists(self.include_target):
            for root, _, files in os.walk(self.include_target):
                for f in files:
                    if f.endswith('.h'):
                        with open(os.path.join(root, f), 'r', errors='ignore') as file:
                            content = file.read()
                            for pat in patterns:
                                self.existing_types.update(pat.findall(content))
        print(f"    Indexed {len(self.existing_types)} existing types.")

    def map_signatures(self):
        """Pass 2: Extract signatures and types requiring forward declaration"""
        print("  [>] Pass 2: Mapping Linkage...")
        func_pat = re.compile(r'^(?:static\s+)?([\w\*]+\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        type_in_param_pat = re.compile(r'\b([a-zA-Z_]\w*)\s*\*') # Only forward declare pointers
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for full_sig, name, params in func_pat.findall(content):
                            # Remove 'static' and clean whitespace
                            clean_sig = " ".join(full_sig.replace('static ', '').split())
                            self.func_signatures[name] = clean_sig
                            
                            # Find pointer types that might need forward declaration
                            for t_name in type_in_param_pat.findall(params):
                                if t_name not in self.existing_types:
                                    self.types_used_in_signatures.add(t_name)

    def generate_header(self):
        """Pass 4: Create a conflict-free global header"""
        print("  [>] Pass 4: Generating Harmonized Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            f.write("#include <ultra64.h> // Force base types like s32/f32 first\n")
            f.write("#include <stdint.h>\n#include <stdbool.h>\n\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            # Forward declarations
            f.write("/* Forward declarations for engine types */\n")
            for t in sorted(self.types_used_in_signatures):
                f.write(f"struct {t};\ntypedef struct {t} {t};\n")
            
            # Function declarations
            f.write("\n/* ==== Weak Linkage Signatures ==== */\n")
            for name, sig in sorted(self.func_signatures.items()):
                f.write(f"__attribute__((weak)) extern {sig};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def apply_linkage(self):
        """Pass 3: Strip static and force inclusion"""
        print("  [>] Pass 3: Promoting Global Linkage...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                    
                    # Remove static from functions and globals
                    content = re.sub(r'^static\s+', '', content, flags=re.MULTILINE)
                    # Inject header if missing
                    if 'harmonized_globals.h' not in content:
                        content = '#include "harmonized_globals.h"\n' + content
                    
                    with open(path, 'w') as file:
                        file.write(content)

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v8.8 Platinum ---\n"
            "include_directories(include)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fcommon -w -O3\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--allow-multiple-definition\")\n"
            "file(GLOB_RECURSE ALL_SRC \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_SRC})\n"
            "# -------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files()
        self.parse_existing_definitions()
        self.map_signatures()
        self.apply_linkage()
        self.generate_header()
        self.patch_cmake()
        print("--- v8.8 Complete ---")

if __name__ == "__main__":
    h = SourceHarmonizerV8_8("Android/app/src/main/cpp", "decomp-files")
    h.run()
