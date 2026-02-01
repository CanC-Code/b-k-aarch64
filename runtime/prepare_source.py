import os
import shutil
import re

class SourceHarmonizerV8_0:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")
        self.type_definitions = {} 
        self.global_symbols = {}
        self.func_signatures = {}

    def parse_typedefs(self):
        print("  [>] Pass 1: Global Semantic Analysis...")
        # Captures core N64 types to ensure the Harmonizer treats them as valid types
        typedef_pat = re.compile(r'typedef\s+(.+)\s+(\w+);')
        struct_pat = re.compile(r'struct\s+(\w+)')
        for root, _, files in os.walk(os.path.join(self.decomp_path, "include")):
            for f in files:
                if f.endswith('.h'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for base, name in typedef_pat.findall(content): self.type_definitions[name] = base
                        for name in struct_pat.findall(content): self.type_definitions[name] = "struct"

    def index_all_symbols(self):
        print("  [>] Pass 2: Linkage Mapping...")
        blacklist = {'main', 'memcpy', 'memset', 'memmove', 'sprintf', 'sqrt', 'sin', 'cos'}
        # Fixed Regex: Now correctly handles pointers and complex return types with potential static prefix
        func_pat = re.compile(r'^(?:static\s+)?([\w\*]+\s+[\w\*]+\s*\(.*?\))\s*\{', re.MULTILINE)
        sym_pat = re.compile(r'^(?:static\s+)?([\w\*]+)\s+([a-zA-Z_]\w*)\s*[;=\[]', re.MULTILINE)
        
        for root, _, files in os.walk(self.decomp_path):
            for f in files:
                if f.endswith(('.c', '.h')):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        # Extract Function Names for indexing
                        for full_sig, _ in re.findall(r'^((?:static\s+)?[\w\*]+\s+([a-zA-Z_]\w*)\s*\(.*?\))\s*\{', content, re.M):
                            name = re.search(r'([a-zA-Z_]\w*)\s*\(', full_sig).group(1)
                            if name not in blacklist: 
                                # Strip 'static' from the stored signature
                                self.func_signatures[name] = full_sig.replace('static ', '').strip()
                        
                        for dtype, sym in sym_pat.findall(content):
                            if sym not in blacklist: self.global_symbols[sym] = dtype

    def promote_and_clean(self):
        """
        v8.0 Fix: Strips 'static' to solve 'Undefined Reference' 
        and removes incompatible N64 attributes.
        """
        print("  [>] Pass 3: Static Promotion & Attribute Cleanup...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    
                    # 1. Promote static functions to global
                    content = re.sub(r'^static\s+(\w+\s+\w+\s*\(.*?\)\s*\{)', r'\1', content, flags=re.MULTILINE)
                    # 2. Strip N64 alignment attributes that confuse Clang in some contexts
                    content = re.sub(r'__attribute__\(\(aligned\(\d+\)\)\)', '', content)
                    
                    if 'harmonized_globals.h' not in content:
                        content = '#include "harmonized_globals.h"\n' + content
                    
                    with open(path, 'w') as file: file.write(content)

    def generate_final_header(self):
        print("  [>] Pass 4: Generating Linker-Safe Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        os.makedirs(self.include_target, exist_ok=True)
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n")
            # Vital for NDK: Ensure standard types are loaded before our weak declarations
            f.write("#include <string.h>\n#include <math.h>\n#include <stdint.h>\n#include <stdarg.h>\n")
            
            for name, base in self.type_definitions.items():
                if base == "struct": f.write(f"struct {name};\n")

            for name, sig in self.func_signatures.items():
                f.write(f"__attribute__((weak)) extern {sig};\n")
            
            for sym, dtype in self.global_symbols.items():
                if sym.startswith(('D_', 'g', 'bgs', 'B_')):
                    clean_type = dtype if dtype in self.type_definitions or dtype.endswith('*') else 'void'
                    # Use array bracket to solve 'Multiple Definition' via Common Symbol resolution
                    f.write(f"__attribute__((weak)) extern {clean_type} {sym}[];\n")
            
            f.write("#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def sync_files(self):
        for sub in ["src", "include"]:
            target = os.path.join(self.android_path, sub)
            source = os.path.join(self.decomp_path, sub)
            if os.path.exists(source):
                if os.path.exists(target): shutil.rmtree(target)
                shutil.copytree(source, target)

    def patch_cmake(self):
        print("  [>] Finalizing CMake for v8.0...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            content = re.sub(r'# --- Harmonizer v[0-9]\.[0-9].*?# ---+', '', content, flags=re.DOTALL)
            injection = (
                "\n# --- Harmonizer v8.0 Gold Master ---\n"
                "include_directories(include)\n"
                "add_definitions(-D__arm64__ -D_LANGUAGE_C -DN_AUDIO)\n"
                "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -fcommon -w -O3 -fno-strict-aliasing\")\n"
                "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\" \"src/*.cpp\")\n"
                "target_sources(bkawrapper PRIVATE ${ALL_C_FILES})\n"
                "target_link_libraries(bkawrapper log z m)\n"
                "# -----------------------------------\n"
            )
            with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        print("--- Harmonizer v8.0: The Gold Master ---")
        self.parse_typedefs()
        self.sync_files()
        self.index_all_symbols()
        self.generate_final_header()
        self.promote_and_clean()
        self.patch_cmake()
        print("--- v8.0 Complete ---")

if __name__ == "__main__":
    h = SourceHarmonizerV8_0("Android/app/src/main/cpp", "decomp-files")
    h.run()
