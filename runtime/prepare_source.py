import os
import shutil
import re

class SourceHarmonizerV7_8:
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
        """
        New for v7.8: Pre-scans headers to understand the project's type system.
        Ensures 'Actor' is known as a struct and 'u32' as an int before processing.
        """
        print("  [>] Pass 1: Semantic Type Analysis...")
        typedef_pat = re.compile(r'typedef\s+(.+)\s+(\w+);')
        struct_pat = re.compile(r'struct\s+(\w+)')
        
        for root, _, files in os.walk(os.path.join(self.decomp_path, "include")):
            for f in files:
                if f.endswith('.h'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for base, name in typedef_pat.findall(content):
                            self.type_definitions[name] = base
                        for name in struct_pat.findall(content):
                            self.type_definitions[name] = "struct"

    def index_all_symbols(self):
        print("  [>] Pass 2: Context-Aware Indexing...")
        blacklist = {'main', 'memcpy', 'memset', 'memmove', 'sprintf', 'sqrt', 'sin', 'cos'}
        # Capture: Type Name(Args) or Type Name; or Type Name[Size];
        func_pat = re.compile(r'^([\w\*]+\s+([a-zA-Z_]\w*)\s*\(.*?\))\s*\{', re.MULTILINE)
        sym_pat = re.compile(r'^([\w\*]+)\s+([a-zA-Z_]\w*)\s*[;=\[]', re.MULTILINE)
        
        for root, _, files in os.walk(self.decomp_path):
            for f in files:
                if f.endswith(('.c', '.h')):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for sig, name in func_pat.findall(content):
                            if name not in blacklist: self.func_signatures[name] = sig
                        for dtype, sym in sym_pat.findall(content):
                            if sym not in blacklist: self.global_symbols[sym] = dtype
        
        print(f"      [+] Resolved {len(self.global_symbols)} typed symbols.")

    def inject_global_header(self):
        """
        Generates a master header that uses discovered types to avoid conflicts.
        """
        print("  [>] Pass 3: Injecting Semantic Global Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        os.makedirs(self.include_target, exist_ok=True)
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n")
            f.write("#include <string.h>\n#include <math.h>\n#include <stdint.h>\n")
            
            # Forward declare structs found in Pass 1 to prevent 'incomplete type' errors
            for name, base in self.type_definitions.items():
                if base == "struct": f.write(f"struct {name};\n")

            for name, sig in self.func_signatures.items():
                f.write(f"__attribute__((weak)) extern {sig};\n")
            
            for sym, dtype in self.global_symbols.items():
                if sym.startswith(('D_', 'g', 'bgs')):
                    # Use semantic type if found, otherwise use void
                    clean_type = dtype if dtype in self.type_definitions or dtype.endswith('*') else 'void'
                    f.write(f"__attribute__((weak)) extern {clean_type} {sym};\n")
            
            f.write("#ifdef __cplusplus\n}\n#endif\n#endif\n")

        # Force include harmonized_globals.h in every .c file
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    if 'harmonized_globals.h' not in content:
                        with open(path, 'w') as file: file.write('#include "harmonized_globals.h"\n' + content)

    def sync_files(self):
        print("  [>] Syncing source...")
        for sub in ["src", "include"]:
            target = os.path.join(self.android_path, sub)
            source = os.path.join(self.decomp_path, sub)
            if os.path.exists(source):
                if os.path.exists(target): shutil.rmtree(target)
                shutil.copytree(source, target)

    def patch_cmake(self):
        print("  [>] Finalizing CMake for v7.8...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            content = re.sub(r'# --- Harmonizer v[0-9]\.[0-9].*?# ---+', '', content, flags=re.DOTALL)
            injection = (
                "\n# --- Harmonizer v7.8 Final Build Logic ---\n"
                "include_directories(include)\n"
                "add_definitions(-D__arm64__)\n"
                "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -fcommon -w\")\n"
                "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\" \"src/*.cpp\")\n"
                "target_sources(bkawrapper PRIVATE ${ALL_C_FILES})\n"
                "target_link_libraries(bkawrapper log z m)\n"
                "# ------------------------------------------\n"
            )
            with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        print("--- Harmonizer v7.8: Semantic Resolution ---")
        self.parse_typedefs()
        self.sync_files()
        self.index_all_symbols()
        self.inject_global_header()
        self.patch_cmake()
        print("--- v7.8 Complete ---")

if __name__ == "__main__":
    h = SourceHarmonizerV7_8("Android/app/src/main/cpp", "decomp-files")
    h.run()
