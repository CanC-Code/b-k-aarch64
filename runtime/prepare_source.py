import os
import shutil
import re

class SourceHarmonizerV10_1:
    def __init__(self, android_path, decomp_path):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        self.cmake_file = os.path.join(self.android_path, "CMakeLists.txt")
        self.func_signatures = {}
        self.var_declarations = {}
        self.primitives = {'int', 'char', 'float', 'double', 'short', 'long', 'void', 'bool',
                           's8', 'u8', 's16', 'u16', 's32', 'u32', 's64', 'u64', 'f32', 'f64', 'u32_t'}

    def sync_files(self):
        print("  [>] Pass 0: Absolute Syncing...")
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
        print("  [>] Pass 1: Omega Shim Mapping...")
        # Matches global function definitions
        func_pat = re.compile(r'^(?:static\s+)?([\w\*]+\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        # Matches global variable definitions (simple)
        var_pat = re.compile(r'^static\s+([\w\*\[\] ]+)\s+([a-zA-Z_]\w*)\s*[:=;]', re.MULTILINE)
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        
                        # Process Functions
                        for full_sig, name, params in func_pat.findall(content):
                            sig = " ".join(full_sig.replace('static ', '').split())
                            words = re.findall(r'\b[a-zA-Z_]\w*\b', sig)
                            for w in set(words):
                                if w not in self.primitives and not w.endswith('_t') and w != 'struct':
                                    sig = re.sub(fr'\b{w}\s*(?=\*)', 'void ', sig)
                            self.func_signatures[name] = sig

                        # Process Variables
                        for var_type, var_name in var_pat.findall(content):
                            # Treat all global pointers as void* for the shim
                            clean_type = "void*" if "*" in var_type else "int"
                            self.var_declarations[var_name] = clean_type

    def promote_linkage(self):
        print("  [>] Pass 2: Global Scope Injection...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                    
                    # Regex replace to remove 'static' only at start of line or after newline
                    content = re.sub(r'^(static\s+)', '', content, flags=re.MULTILINE)
                    
                    # Append header fallback
                    if 'harmonized_globals.h' not in content:
                        content += '\n#include "harmonized_globals.h"\n'
                        
                    with open(path, 'w') as file:
                        file.write(content)

    def generate_header(self):
        print("  [>] Pass 3: Generating Final Fallback Shim...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <ultra64.h>\n#include <stdint.h>\n#include <stddef.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            f.write("/* Function Shims */\n")
            for name, sig in sorted(self.func_signatures.items()):
                f.write(f"__attribute__((weak, visibility(\"default\"))) extern {sig};\n")
            
            f.write("\n/* Variable Shims */\n")
            for name, vtype in sorted(self.var_declarations.items()):
                # Declaring weak extern variables solves the 'static' visibility issue across files
                f.write(f"__attribute__((weak)) extern {vtype} {name};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v10.1 Absolute Omega ---\n"
            "include_directories(include)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fcommon -O3 -w -fno-builtin\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--allow-multiple-definition\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C -DFCOMMON)\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# ---------------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files()
        self.map_linkage()
        self.promote_linkage()
        self.generate_header()
        self.patch_cmake()
        print("--- v10.1 Absolute Omega: Fully Automated ---")

if __name__ == "__main__":
    h = SourceHarmonizerV10_1("Android/app/src/main/cpp", "decomp-files")
    h.run()
