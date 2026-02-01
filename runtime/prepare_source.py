import os
import shutil
import re

class SourceHarmonizerV8_7:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")
        self.global_symbols = {}
        self.func_signatures = {}
        self.existing_types = set()
        self.types_used_in_signatures = set()

    def sync_files(self):
        """Intelligently sync files - copy only from decomp, preserve existing Android files"""
        print("  [>] Syncing Files (preserving existing Android files)...")
        for sub in ["src", "include"]:
            source = os.path.join(self.decomp_path, sub)
            target = os.path.join(self.android_path, sub)
            if os.path.exists(source):
                if os.path.exists(target):
                    has_android_files = any(
                        os.path.exists(os.path.join(target, f)) 
                        for f in ['jni', 'cpp', 'NativeBridge.cpp', 'NativeBridge.h']
                    )
                    if not has_android_files:
                        shutil.rmtree(target)
                        shutil.copytree(source, target)
                    else:
                        print(f"    Preserving existing {sub} directory with Android files")
                        for root, dirs, files in os.walk(source):
                            rel_path = os.path.relpath(root, source)
                            target_dir = os.path.join(target, rel_path)
                            os.makedirs(target_dir, exist_ok=True)
                            for file in files:
                                src_file = os.path.join(root, file)
                                dst_file = os.path.join(target_dir, file)
                                if not os.path.exists(dst_file):
                                    shutil.copy2(src_file, dst_file)
                else:
                    shutil.copytree(source, target)

    def parse_typedefs(self):
        """Pass 1: Discovery of all types already defined in project headers"""
        print("  [>] Pass 1: Global Type Discovery...")
        if not os.path.exists(self.include_target): return
        
        # Patterns to find existing definitions to avoid 'Redefinition' errors
        patterns = [
            re.compile(r'typedef\s+(?:struct|union|enum)\s+\w*\s*\{[^}]*\}\s*([a-zA-Z_]\w*)\s*;', re.DOTALL),
            re.compile(r'}\s*([a-zA-Z_]\w*)\s*;'),
            re.compile(r'typedef\s+[\w\s\*]+\s+([a-zA-Z_]\w*)\s*;'),
            re.compile(r'enum\s+([a-zA-Z_]\w*)\s*\{'),
            re.compile(r'typedef\s+struct\s+([a-zA-Z_]\w*)\s+\1\s*;')
        ]

        for root, _, files in os.walk(self.include_target):
            for f in files:
                if f.endswith('.h'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for pat in patterns:
                            self.existing_types.update(pat.findall(content))
        
        # Hard-blacklist standard types that should never be forward-declared
        self.existing_types.update(['size_t', 'ssize_t', 'intptr_t', 'uintptr_t', 'FILE', 'va_list'])
        print(f"    Indexed {len(self.existing_types)} existing types from headers.")

    def index_all_symbols(self):
        """Pass 2: Map signatures and extract types requiring forward declaration"""
        print("  [>] Pass 2: Mapping Absolute Linkage...")
        blacklist = {'main', 'memcpy', 'memset', 'memmove', 'sprintf', 'sqrt', 'sin', 'cos', 'long', 'unsigned'}
        primitives = {'void', 'int', 'char', 'float', 'double', 'short', 'uint8_t', 'int32_t', 'u32', 's32', 'f32', 'u8', 's8', 'u16', 's16', 'bool'}
        
        func_pat = re.compile(r'^(?:static\s+)?([\w\*]+\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        sym_pat = re.compile(r'^(?:static\s+)?([\w\*]+)\s+([a-zA-Z_]\w*)\s*[;=\[]', re.MULTILINE)
        
        # Improved regex to catch pointer types and struct-prefixed types
        type_in_param_pat = re.compile(r'\b(?:struct\s+)?([a-zA-Z_]\w*)\s*\*')
        
        scan_paths = [self.decomp_path, self.src_target]
        for base_path in scan_paths:
            if not os.path.exists(base_path): continue
            for root, _, files in os.walk(base_path):
                for f in files:
                    if f.endswith(('.c', '.h')):
                        with open(os.path.join(root, f), 'r', errors='ignore') as file:
                            content = file.read()
                            # Index Functions
                            for full_sig, name, params in func_pat.findall(content):
                                if name not in blacklist:
                                    self.func_signatures[name] = " ".join(full_sig.replace('static ', '').split())
                                    for t_name in type_in_param_pat.findall(params):
                                        if t_name not in primitives and t_name not in blacklist:
                                            self.types_used_in_signatures.add(t_name)
                            # Index Global Symbols
                            for dtype, sym in sym_pat.findall(content):
                                if sym not in blacklist: self.global_symbols[sym] = dtype
        
        print(f"    Found {len(self.func_signatures)} signatures and {len(self.types_used_in_signatures)} candidate types.")

    def generate_final_header(self):
        """Pass 4: Create the harmonized header without redefinition conflicts"""
        print("  [>] Pass 4: Generating Large-Model Global Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        # Only forward declare if it's used in a signature but NOT defined anywhere else
        types_to_declare = self.types_used_in_signatures - self.existing_types
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            f.write("#include <stdint.h>\n#include <stdbool.h>\n#include <stddef.h>\n#include <stdarg.h>\n\n")
            
            if types_to_declare:
                f.write("/* Forward declarations for types not found in include/ headers */\n")
                for type_name in sorted(types_to_declare):
                    if not type_name.isdigit(): # Safety check
                        f.write(f"typedef struct {type_name} {type_name};\n")
                f.write("\n")
            
            if self.func_signatures:
                f.write("/* ==== Weak Function Declarations ==== */\n")
                for name, sig in sorted(self.func_signatures.items()):
                    f.write(f"__attribute__((weak)) extern {sig};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def promote_and_clean(self):
        """Remove static keywords to allow global linkage"""
        print("  [>] Pass 3: Promoting Linkage (stripping static)...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    content = re.sub(r'^static\s+', '', content, flags=re.MULTILINE)
                    content = re.sub(r'__attribute__\(\(aligned\(\d+\)\)\)', '', content)
                    if 'harmonized_globals.h' not in content:
                        content = '#include "harmonized_globals.h"\n' + content
                    with open(path, 'w') as file: file.write(content)

    def patch_cmake(self):
        """Update CMake to support the large memory model and common linkage"""
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer v[0-9]\.[0-9].*?# ---+', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v8.7 Platinum Edition ---\n"
            "include_directories(include)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fcommon -w -O3 -fno-strict-aliasing\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--allow-multiple-definition\")\n"
            "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C_FILES})\n"
            "# ----------------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        print("--- Harmonizer v8.7: Platinum Edition ---")
        self.sync_files()
        self.parse_typedefs()
        self.index_all_symbols()
        self.generate_final_header()
        self.promote_and_clean()
        self.patch_cmake()
        print("--- v8.7 Complete: Ready for Ninja Build ---")

if __name__ == "__main__":
    # Ensure paths are correct for your environment
    h = SourceHarmonizerV8_7("Android/app/src/main/cpp", "decomp-files")
    h.run()
