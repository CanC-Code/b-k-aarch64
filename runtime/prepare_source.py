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
        """Intelligently sync files - preserve existing Android build files"""
        print("  [>] Syncing Files...")
        for sub in ["src", "include"]:
            source = os.path.join(self.decomp_path, sub)
            target = os.path.join(self.android_path, sub)
            if os.path.exists(source):
                if os.path.exists(target):
                    has_android = any(os.path.exists(os.path.join(target, f)) for f in ['jni', 'cpp', 'NativeBridge.cpp'])
                    if not has_android:
                        shutil.rmtree(target)
                        shutil.copytree(source, target)
                    else:
                        for root, _, files in os.walk(source):
                            rel = os.path.relpath(root, source)
                            os.makedirs(os.path.join(target, rel), exist_ok=True)
                            for file in files:
                                if not os.path.exists(os.path.join(target, rel, file)):
                                    shutil.copy2(os.path.join(root, file), os.path.join(target, rel, file))
                else:
                    shutil.copytree(source, target)

    def parse_typedefs(self):
        """Pass 1: Aggressive discovery of types to prevent redefinition errors"""
        print("  [>] Pass 1: Global Type Discovery...")
        if not os.path.exists(self.include_target): return
        
        # Expanded patterns to catch: typedef struct Name, enum Name, } Name;
        patterns = [
            re.compile(r'typedef\s+(?:struct|union|enum)\s+([a-zA-Z_]\w*)'),
            re.compile(r'}\s*([a-zA-Z_]\w*)\s*;'),
            re.compile(r'typedef\s+[\w\s\*]+\s+([a-zA-Z_]\w*)\s*;'),
            re.compile(r'enum\s+([a-zA-Z_]\w*)\s*\{'),
            re.compile(r'#define\s+([a-zA-Z_]\w*)\b') # Catch types hidden behind macros
        ]

        for root, _, files in os.walk(self.include_target):
            for f in files:
                if f.endswith('.h'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for pat in patterns:
                            self.existing_types.update(pat.findall(content))
        
        # Hard-blacklist standard and system types
        self.existing_types.update([
            'size_t', 'ssize_t', 'intptr_t', 'uintptr_t', 'FILE', 'va_list', 
            'uint8_t', 'int32_t', 'uint32_t', 'u32', 's32', 'f32', 'u8', 's8', 'u64'
        ])
        print(f"    Indexed {len(self.existing_types)} existing types.")

    def index_all_symbols(self):
        """Pass 2: Map signatures and track pointer types"""
        print("  [>] Pass 2: Mapping Absolute Linkage...")
        blacklist = {'main', 'memcpy', 'memset', 'memmove', 'sprintf', 'sqrt', 'sin', 'cos', 'long', 'unsigned', 'const'}
        primitives = {'void', 'int', 'char', 'float', 'double', 'short', 'bool', 'unsigned', 'signed'}
        
        func_pat = re.compile(r'^(?:static\s+)?([\w\*]+\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        sym_pat = re.compile(r'^(?:static\s+)?([\w\*]+)\s+([a-zA-Z_]\w*)\s*[;=\[]', re.MULTILINE)
        
        # Improved regex to catch pointer types (e.g., Actor*, struct Actor *)
        type_in_param_pat = re.compile(r'\b(?:struct\s+)?([a-zA-Z_]\w*)\s*\*')
        
        scan_paths = [self.decomp_path, self.src_target]
        for base_path in scan_paths:
            if not os.path.exists(base_path): continue
            for root, _, files in os.walk(base_path):
                for f in files:
                    if f.endswith(('.c', '.h')):
                        with open(os.path.join(root, f), 'r', errors='ignore') as file:
                            content = file.read()
                            for full_sig, name, params in func_pat.findall(content):
                                if name not in blacklist:
                                    self.func_signatures[name] = " ".join(full_sig.replace('static ', '').split())
                                    for t_name in type_in_param_pat.findall(params):
                                        if t_name not in primitives and t_name not in blacklist:
                                            self.types_used_in_signatures.add(t_name)
                            for dtype, sym in sym_pat.findall(content):
                                if sym not in blacklist: self.global_symbols[sym] = dtype
        
        print(f"    Found {len(self.func_signatures)} signatures.")

    def generate_final_header(self):
        """Pass 4: Generate header using only truly unknown types"""
        print("  [>] Pass 4: Generating Large-Model Global Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        # CRITICAL: Only forward declare if it is NOT already in our existing_types index
        types_to_declare = self.types_used_in_signatures - self.existing_types
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            f.write("#include <stdint.h>\n#include <stdbool.h>\n#include <stddef.h>\n#include <stdarg.h>\n\n")
            
            if types_to_declare:
                f.write("/* Forward declarations for unknown types */\n")
                for type_name in sorted(types_to_declare):
                    if len(type_name) > 2: # Ignore accidental 1-2 char captures
                        f.write(f"typedef struct {type_name} {type_name};\n")
                f.write("\n")
            
            if self.func_signatures:
                f.write("/* ==== Weak Function Declarations ==== */\n")
                for name, sig in sorted(self.func_signatures.items()):
                    # Sanitize signature to ensure no 'static' remains
                    clean_sig = sig.replace('static ', '')
                    f.write(f"__attribute__((weak)) extern {clean_sig};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def promote_and_clean(self):
        """Strip static and inject the global header"""
        print("  [>] Pass 3: Promoting Linkage...")
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
        """Update CMake for cross-module linkage and ARM64/Large Model"""
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
            "target_link_libraries(bkawrapper log z m)\n"
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
    h = SourceHarmonizerV8_7("Android/app/src/main/cpp", "decomp-files")
    h.run()
