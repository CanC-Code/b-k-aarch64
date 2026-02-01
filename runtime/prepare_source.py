import os
import shutil
import re

class SourceHarmonizerV7_5:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")
        self.global_symbols = set()
        self.func_signatures = set()

    def index_all_symbols(self):
        """
        Pass 1: Complete Project Mapping.
        Extracts names and basic function signatures to create forward declarations.
        """
        print("  [>] Pass 1: Global Symbol Indexing...")
        func_pat = re.compile(r'^(\w+\s+\w+\s*\(.*?\))\s*\{', re.MULTILINE)
        sym_pat = re.compile(r'^[a-zA-Z_]\w*\s+([a-zA-Z_]\w*)\s*[;=\[]', re.MULTILINE)
        
        for root, _, files in os.walk(self.decomp_path):
            for f in files:
                if f.endswith(('.c', '.h')):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        self.func_signatures.update(func_pat.findall(content))
                        self.global_symbols.update(sym_pat.findall(content))
        
        self.global_symbols.update(['Actor', 'Gfx', 'Mtx', 'Vtx', 'u32', 's32', 'f32', 'u8', 's8'])
        print(f"      [+] Indexed {len(self.global_symbols)} symbols and {len(self.func_signatures)} signatures.")

    def inject_global_header(self):
        """
        New for v7.5: Creates a master header so every file sees every symbol.
        This fixes the 'undeclared identifier' errors once and for all.
        """
        print("  [>] Pass 2: Injecting Global Visibility Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        os.makedirs(self.include_target, exist_ok=True)
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <string.h>\n#include <math.h>\n")
            # Forward declare functions
            for sig in self.func_signatures:
                f.write(f"extern {sig};\n")
            # Forward declare known large globals
            for sym in self.global_symbols:
                if sym.startswith('D_') or sym.startswith('g'):
                    f.write(f"extern void* {sym};\n")
            f.write("#endif\n")

        # Force include this header in every .c file
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
        print(f"      [!] Patched {patched} array initializers.")

    def sync_files(self):
        print(f"  [>] Syncing source...")
        for sub in ["src", "include"]:
            target = os.path.join(self.android_path, sub)
            source = os.path.join(self.decomp_path, sub)
            if os.path.exists(source):
                if os.path.exists(target): shutil.rmtree(target)
                shutil.copytree(source, target)

    def patch_cmake(self):
        print("  [>] Finalizing CMake for v7.5...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            content = re.sub(r'# --- Harmonizer v[0-9]\.[0-9].*?# ---+', '', content, flags=re.DOTALL)
            injection = (
                "\n# --- Harmonizer v7.5 Discovery ---\n"
                "include_directories(include)\n"
                "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\" \"src/*.cpp\")\n"
                "target_sources(bkawrapper PRIVATE ${ALL_C_FILES})\n"
                "target_link_libraries(bkawrapper log z m)\n"
                "# ----------------------------------\n"
            )
            with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        print("--- Harmonizer v7.5: Global Visibility Fix ---")
        self.index_all_symbols()
        self.sync_files()
        self.inject_global_header()
        self.fix_array_initializers()
        self.patch_cmake()
        print("--- v7.5 Complete ---")

if __name__ == "__main__":
    h = SourceHarmonizerV7_5("Android/app/src/main/cpp", "decomp-files")
    h.run()
