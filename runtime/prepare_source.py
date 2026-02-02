import os
import shutil
import re

class SourceHarmonizerV9_3:
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
        print("  [>] Pass 0: Robust Syncing...")
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
                    src_file = os.path.join(root, f)
                    dst_file = os.path.join(dest_dir, f)
                    if not os.path.exists(dst_file):
                        shutil.copy2(src_file, dst_file)

    def parse_definitions(self):
        print("  [>] Pass 1: Global Type Indexing...")
        # Hardcore protection for engine and system primitives
        self.existing_types.update([
            's8', 'u8', 's16', 'u16', 's32', 'u32', 's64', 'u64', 'f32', 'f64',
            'Vtx', 'Mtx', 'Gfx', 'u_long', 'u_short', 'u_int', 'u_char', 'bool',
            'size_t', 'uintptr_t', 'intptr_t', 'void', 'char', 'int', 'long', 'float'
        ])
        
        patterns = [
            re.compile(r'typedef\s+(?:struct|union|enum)?\s*[\w\s\*]+\s+([a-zA-Z_]\w*)\s*;'),
            re.compile(r'}\s*([a-zA-Z_]\w*)\s*;'),
            re.compile(r'(?:struct|union|enum)\s+([a-zA-Z_]\w*)\s*\{')
        ]

        for root, _, files in os.walk(self.include_target):
            for f in files:
                if f.endswith('.h'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for pat in patterns:
                            self.existing_types.update(pat.findall(content))

    def map_linkage(self):
        print("  [>] Pass 2: Deep Signature Analysis...")
        # Matches global function definitions
        func_pat = re.compile(r'^(?:static\s+)?([\w\*]+\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        
        # SMARTER REGEX: Catch any word preceding a '*' even inside function pointers
        # This catches "BKModel *", "BKVtxRef *", etc. inside "(void (*fn)(s32, BKVtxRef *, ...))"
        deep_ptr_pat = re.compile(r'\b([a-zA-Z_]\w*)\s*(?=\*)')
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for full_sig, name, params in func_pat.findall(content):
                            # Clean and store signature
                            clean_sig = " ".join(full_sig.replace('static ', '').split())
                            self.func_signatures[name] = clean_sig
                            
                            # Deep search for types needing forward declaration
                            for t_name in deep_ptr_pat.findall(full_sig):
                                if t_name not in self.existing_types and not t_name.endswith('_t'):
                                    self.types_to_forward_declare.add(t_name)

    def promote_linkage(self):
        print("  [>] Pass 3: Globalizing Scope...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith(('.c', '.h')):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        lines = file.readlines()
                    
                    output = []
                    last_inc_idx = -1
                    for i, line in enumerate(lines):
                        # ONLY strip 'static' if it starts the line (prevents breaking local statics)
                        processed = re.sub(r'^static\s+', '', line)
                        output.append(processed)
                        if '#include' in line:
                            last_inc_idx = i

                    # Inject harmonized header AFTER all other includes
                    if f.endswith('.c'):
                        injection = '\n#include "harmonized_globals.h"\n'
                        if last_inc_idx != -1:
                            output.insert(last_inc_idx + 1, injection)
                        else:
                            output.insert(0, injection)
                        
                    with open(path, 'w') as file:
                        file.writelines(output)

    def generate_header(self):
        print("  [>] Pass 4: Generating Super-Platinum Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            # Force core types first
            f.write("#include <ultra64.h>\n#include <stdint.h>\n#include <stdbool.h>\n#include <stddef.h>\n\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            if self.types_to_forward_declare:
                f.write("/* Opaque Type Forward Declarations */\n")
                for t in sorted(self.types_to_forward_declare):
                    # Pure struct declaration is most compatible for pointers
                    f.write(f"struct {t};\n")
                f.write("\n")
                
                f.write("/* Compatibility Typedefs */\n")
                for t in sorted(self.types_to_forward_declare):
                    f.write(f"#ifndef _HARM_TYPEDEF_{t}\n#define _HARM_TYPEDEF_{t}\ntypedef struct {t} {t};\n#endif\n")
                f.write("\n")
            
            f.write("/* Weak Global Linkage Signatures */\n")
            for name, sig in sorted(self.func_signatures.items()):
                # Added visibility default to ensure JNI can see these
                f.write(f"__attribute__((weak, visibility(\"default\"))) extern {sig};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v9.3 Super-Platinum ---\n"
            "include_directories(include)\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C -DFCOMMON -D_GNU_SOURCE)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fcommon -w -O3 -fno-strict-aliasing -funsafe-math-optimizations\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--allow-multiple-definition -Wl,--no-undefined\")\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# --------------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files()
        self.parse_definitions()
        self.map_linkage()
        self.promote_linkage()
        self.generate_header()
        self.patch_cmake()
        print("--- Harmonization v9.3 Complete ---")

if __name__ == "__main__":
    h = SourceHarmonizerV9_3("Android/app/src/main/cpp", "decomp-files")
    h.run()
