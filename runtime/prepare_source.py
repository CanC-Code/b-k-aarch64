import os
import shutil
import re

class SourceHarmonizerV7_7:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")
        self.global_symbols = {} # Map symbol name to its detected type context
        self.func_signatures = {}

    def index_all_symbols(self):
        print("  [>] Pass 1: Linker-Aware Symbol Indexing...")
        blacklist = {'main', 'memcpy', 'memset', 'memmove', 'sprintf', 'sqrt', 'sin', 'cos'}
        
        # Improved patterns to capture the type context of data symbols
        func_pat = re.compile(r'^(\w+\s+([a-zA-Z_]\w*)\s*\(.*?\))\s*\{', re.MULTILINE)
        sym_pat = re.compile(r'^(\w+)\s+([a-zA-Z_]\w*)\s*[;=\[]', re.MULTILINE)
        
        for root, _, files in os.walk(self.decomp_path):
            for f in files:
                if f.endswith(('.c', '.h')):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for sig, name in func_pat.findall(content):
                            if name not in blacklist:
                                self.func_signatures[name] = sig
                        for dtype, sym in sym_pat.findall(content):
                            if sym not in blacklist:
                                self.global_symbols[sym] = dtype
        
        print(f"      [+] Indexed {len(self.global_symbols)} data symbols and {len(self.func_signatures)} functions.")

    def inject_global_header(self):
        """
        Pass 2: Generating a Weak-Linkage Master Header.
        Uses __attribute__((weak)) to allow the linker to ignore duplicate declarations.
        """
        print("  [>] Pass 2: Generating Weak-Linkage Global Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        os.makedirs(self.include_target, exist_ok=True)
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n")
            f.write("#include <string.h>\n#include <math.h>\n#include <stdint.h>\n")
            
            # Use 'weak' attribute to prevent multiple definition errors at link time
            for name, sig in self.func_signatures.items():
                f.write(f"__attribute__((weak)) extern {sig};\n")
            
            for sym, dtype in self.global_symbols.items():
                if sym.startswith('D_') or sym.startswith('g'):
                    # Default to void* if we can't be sure of the type, but preserve context
                    type_str = dtype if dtype != 'extern' else 'void'
                    f.write(f"__attribute__((weak)) extern {type_str} {sym};\n")
            
            f.write("#ifdef __cplusplus\n}\n#endif\n")
            f.write("#endif\n")

        # Smart Injection: Avoid self-reference conflicts
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
                        # Ensure we don't double-include string.h if it's already in harmonized_globals
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
        print("  [>] Finalizing CMake for v7.7...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            content = re.sub(r'# --- Harmonizer v[0-9]\.[0-9].*?# ---+', '', content, flags=re.DOTALL)
            injection = (
                "\n# --- Harmonizer v7.7 Linker Optimization ---\n"
                "include_directories(include)\n"
                "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -fcommon\")\n" # Vital for legacy N64 global symbols
                "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\" \"src/*.cpp\")\n"
                "target_sources(bkawrapper PRIVATE ${ALL_C_FILES})\n"
                "target_link_libraries(bkawrapper log z m)\n"
                "# ------------------------------------------\n"
            )
            with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        print("--- Harmonizer v7.7: Linker Optimization ---")
        self.index_all_symbols()
        self.sync_files()
        self.inject_global_header()
        self.fix_array_initializers()
        self.patch_cmake()
        print("--- v7.7 Complete ---")

if __name__ == "__main__":
    h = SourceHarmonizerV7_7("Android/app/src/main/cpp", "decomp-files")
    h.run()
