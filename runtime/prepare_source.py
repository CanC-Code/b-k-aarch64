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
        self.existing_types = set() # Renamed to track both typedefs and enums
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
        """Comprehensive type extraction to avoid redefinition errors"""
        print("  [>] Pass 1: Global Type Discovery...")
        include_dir = self.include_target
        if not os.path.exists(include_dir):
            return
        
        # Regex to match 'typedef struct/union/enum { ... } Name;' or '}Name;'
        # Improved to catch definitions without spaces after the closing brace
        type_def_pattern = re.compile(r'}\s*([a-zA-Z_]\w*)\s*;')
        # Regex for simple typedefs: 'typedef int Name;'
        simple_typedef_pattern = re.compile(r'typedef\s+(?!struct|union|enum)[\w\s\*]+\s+([a-zA-Z_]\w*)\s*;')
        # Regex for enum names: 'enum Name {'
        enum_name_pattern = re.compile(r'enum\s+([a-zA-Z_]\w*)\s*\{')

        for root, _, files in os.walk(include_dir):
            for f in files:
                if f.endswith('.h'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                        self.existing_types.update(type_def_pattern.findall(content))
                        self.existing_types.update(simple_typedef_pattern.findall(content))
                        self.existing_types.update(enum_name_pattern.findall(content))
        
        print(f"    Found {len(self.existing_types)} existing types")

    def index_all_symbols(self):
        """Index functions and track all types used in signatures"""
        print("  [>] Pass 2: Mapping Absolute Linkage...")
        blacklist = {'main', 'memcpy', 'memset', 'memmove', 'sprintf', 'sqrt', 'sin', 'cos', 'long'}
        
        func_pat = re.compile(r'^(?:static\s+)?([\w\*]+\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        sym_pat = re.compile(r'^(?:static\s+)?([\w\*]+)\s+([a-zA-Z_]\w*)\s*[;=\[]', re.MULTILINE)
        
        # Catch types used as pointers: 'Type *' or 'struct Type*'
        type_in_param_pat = re.compile(r'\b(?:struct\s+)?([a-zA-Z_]\w*)\s*\*')
        
        scan_paths = [self.decomp_path, self.src_target]
        for base_path in scan_paths:
            if not os.path.exists(base_path): continue
            for root, _, files in os.walk(base_path):
                for f in files:
                    if f.endswith(('.c', '.h')):
                        path = os.path.join(root, f)
                        with open(path, 'r', errors='ignore') as file:
                            content = file.read()
                            for full_sig, name, params in func_pat.findall(content):
                                if name not in blacklist: 
                                    self.func_signatures[name] = " ".join(full_sig.replace('static ', '').split())
                                    for type_name in type_in_param_pat.findall(params):
                                        if type_name not in blacklist and len(type_name) > 1:
                                            self.types_used_in_signatures.add(type_name)
                            for dtype, sym in sym_pat.findall(content):
                                if sym not in blacklist: self.global_symbols[sym] = dtype
        
        # Filter out primitives
        primitives = {'void', 'int', 'char', 'float', 'double', 'short', 'uint8_t', 'int32_t', 'u32', 's32', 'f32'}
        self.types_used_in_signatures -= primitives

    def generate_final_header(self):
        """Generate harmonized_globals.h with safe forward declarations"""
        print("  [>] Pass 4: Generating Large-Model Global Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        # Only forward declare types that are used but NOT defined in any header
        types_to_declare = self.types_used_in_signatures - self.existing_types
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            f.write("#include <stdint.h>\n#include <stdbool.h>\n\n")
            
            if types_to_declare:
                f.write("/* Forward declarations for unknown types */\n")
                for type_name in sorted(types_to_declare):
                    f.write(f"typedef struct {type_name} {type_name};\n")
                f.write("\n")
            
            if self.func_signatures:
                f.write("/* ==== Function Declarations ==== */\n")
                for name, sig in sorted(self.func_signatures.items()):
                    f.write(f"__attribute__((weak)) extern {sig};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def promote_and_clean(self):
        """Remove static keywords and alignment attributes"""
        print("  [>] Pass 3: Breaking 4GB Address Barriers...")
        modified = 0
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: 
                        content = file.read()
                    original_content = content
                    content = re.sub(r'^static\s+', '', content, flags=re.MULTILINE)
                    content = re.sub(r'__attribute__\(\(aligned\(\d+\)\)\)', '', content)
                    if 'harmonized_globals.h' not in content:
                        content = '#include "harmonized_globals.h"\n' + content
                    if content != original_content:
                        with open(path, 'w') as file: file.write(content)
                        modified += 1
        print(f"    Modified {modified} source files")

    def patch_cmake(self):
        """Update CMakeLists.txt with necessary compiler flags"""
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer v[0-9]\.[0-9].*?# ---+', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v8.7 Platinum Edition ---\n"
            "include_directories(include)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fcommon -w -O3\")\n"
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
        print("--- v8.7 Complete ---")

if __name__ == "__main__":
    h = SourceHarmonizerV8_7("Android/app/src/main/cpp", "decomp-files")
    h.run()
