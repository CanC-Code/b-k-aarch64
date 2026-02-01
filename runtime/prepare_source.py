import os
import shutil
import re

class SourceHarmonizerV7_6:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")
        self.global_symbols = set()
        self.func_signatures = {} # Changed to dict to track names vs full signatures

    def index_all_symbols(self):
        """
        Pass 1: Intelligent Indexing.
        Avoids indexing symbols that are part of the standard C library 
        or the N64 'Ultra' core to prevent 'conflicting types' errors.
        """
        print("  [>] Pass 1: Type-Safe Symbol Indexing...")
        # Ignore core engine/system functions that often cause conflicts
        blacklist = {'main', 'memcpy', 'memset', 'memmove', 'sprintf', 'sqrt', 'sin', 'cos', 'osInitialize'}
        
        func_pat = re.compile(r'^(\w+\s+([a-zA-Z_]\w*)\s*\(.*?\))\s*\{', re.MULTILINE)
        sym_pat = re.compile(r'^[a-zA-Z_]\w*\s+([a-zA-Z_]\w*)\s*[;=\[]', re.MULTILINE)
        
        for root, _, files in os.walk(self.decomp_path):
            for f in files:
                if f.endswith(('.c', '.h')):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        # Index functions while checking blacklist
                        for sig, name in func_pat.findall(content):
                            if name not in blacklist:
                                self.func_signatures[name] = sig
                        # Index globals
                        for sym in sym_pat.findall(content):
                            if sym not in blacklist:
                                self.global_symbols.add(sym)
        
        print(f"      [+] Indexed {len(self.global_symbols)} symbols and {len(self.func_signatures)} signatures.")

    def inject_global_header(self):
        """
        Generates a master header with 'extern C' safety for modern C++ linkage.
        """
        print("  [>] Pass 2: Generating Type-Safe Global Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        os.makedirs(self.include_target, exist_ok=True)
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n")
            f.write("#include <string.h>\n#include <math.h>\n#include <stdint.h>\n")
            
            # Forward declare functions with the specific signature found
            for name, sig in self.func_signatures.items():
                f.write(f"extern {sig};\n")
            
            # Forward declare data symbols
            for sym in self.global_symbols:
                if sym.startswith('D_') or sym.startswith('g'):
                    f.write(f"extern void* {sym};\n")
            
            f.write("#ifdef __cplusplus\n}\n#endif\n")
            f.write("#endif\n")

        # Force include in all source files
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    if 'harmonized_globals.h' not in content:
                        with open(path, 'w') as file:
                            file.write('#include "harmonized_globals.h"\n' + content)

    def fix_array_initializers(self):
        print("  [>] Pass 3: Repairing Legacy Array Initializers...")
        pattern = re.compile(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);')
        patched = 0
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    if pattern.search(content):
                        new_content = pattern.sub(r'\1 \2[\3]; memmove(\2, \4, \3);', content)
                        with open(path, 'w') as file: file.write(new_content)
                        patched += 1
        print(f"      [!] Patched {patched} initializers.")

    def sync_files(self):
        print(f"  [>] Syncing source...")
        for sub in ["src", "include"]:
            target = os.path.join(self.android_path, sub)
            source = os.path.join(self.decomp_path, sub)
            if os.path.exists(source):
                if os.path.exists(target): shutil.rmtree(target)
                shutil.copytree(source, target)

    def patch_cmake(self):
        print("  [>] Finalizing CMake for v7.6...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            content = re.sub(r'# --- Harmonizer v[0-9]\.[0-9].*?# ---+', '', content, flags=re.DOTALL)
            injection = (
                "\n# --- Harmonizer v7.6 Linker Integrity ---\n"
                "include_directories(include)\n"
                "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\" \"src/*.cpp\")\n"
                "target_sources(bkawrapper PRIVATE ${ALL_C_FILES})\n"
                "target_link_libraries(bkawrapper log z m)\n"
                "# ----------------------------------------\n"
            )
            with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        print("--- Harmonizer v7.6: Type-Safe Linkage ---")
        self.index_all_symbols()
        self.sync_files()
        self.inject_global_header()
        self.fix_array_initializers()
        self.patch_cmake()
        print("--- v7.6 Complete ---")

if __name__ == "__main__":
    h = SourceHarmonizerV7_6("Android/app/src/main/cpp", "decomp-files")
    h.run()
