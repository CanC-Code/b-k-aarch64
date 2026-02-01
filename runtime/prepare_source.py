import os
import shutil
import re

class SourceHarmonizerV8_6:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")
        self.type_definitions = {} 
        self.global_symbols = {}
        self.func_signatures = {}
        self.struct_types = set()
        self.existing_typedefs = set()  # Track types already typedef'd in headers

    def parse_typedefs(self):
        print("  [>] Pass 1: Global Type Discovery...")
        typedef_pat = re.compile(r'typedef\s+(?:struct\s+\w+\s+)?(\w+)\s*;')
        typedef_struct_pat = re.compile(r'typedef\s+struct\s+\w+\s*\{[^}]*\}\s*(\w+)\s*;', re.DOTALL)
        struct_pat = re.compile(r'struct\s+(\w+)')
        
        for root, _, files in os.walk(os.path.join(self.decomp_path, "include")):
            for f in files:
                if f.endswith('.h'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                        
                        # Track all existing typedef names
                        for name in typedef_pat.findall(content):
                            self.existing_typedefs.add(name)
                        for name in typedef_struct_pat.findall(content):
                            self.existing_typedefs.add(name)
                        
                        # Track struct definitions
                        for name in struct_pat.findall(content): 
                            self.type_definitions[name] = "struct"

    def index_all_symbols(self):
        print("  [>] Pass 2: Mapping Absolute Linkage...")
        blacklist = {'main', 'memcpy', 'memset', 'memmove', 'sprintf', 'sqrt', 'sin', 'cos'}
        func_pat = re.compile(r'^(?:static\s+)?([\w\*]+\s+([a-zA-Z_]\w*)\s*\((?:[^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        sym_pat = re.compile(r'^(?:static\s+)?([\w\*]+)\s+([a-zA-Z_]\w*)\s*[;=\[]', re.MULTILINE)
        
        # Pattern to find struct/type names in function signatures
        param_type_pat = re.compile(r'\b((?:struct\s+)?[A-Z][a-zA-Z0-9_]*)\s*\*')
        
        for root, _, files in os.walk(self.decomp_path):
            for f in files:
                if f.endswith(('.c', '.h')):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for full_sig, name in func_pat.findall(content):
                            if name not in blacklist: 
                                clean_sig = " ".join(full_sig.replace('static ', '').split())
                                self.func_signatures[name] = clean_sig
                                
                                # Extract struct types from signature
                                for match in param_type_pat.findall(clean_sig):
                                    # Remove 'struct' prefix if present
                                    type_name = match.replace('struct ', '').strip()
                                    # Skip standard types and already typedef'd types
                                    if (type_name not in {'uint8_t', 'uint16_t', 'uint32_t', 'int8_t', 'int16_t', 'int32_t', 'void'} 
                                        and type_name not in self.existing_typedefs):
                                        self.struct_types.add(type_name)
                                        
                        for dtype, sym in sym_pat.findall(content):
                            if sym not in blacklist: self.global_symbols[sym] = dtype

    def promote_and_clean(self):
        print("  [>] Pass 3: Breaking 4GB Address Barriers...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    
                    # Force globalization and remove N64 alignment that crashes the ARM64 linker
                    content = re.sub(r'^static\s+', '', content, flags=re.MULTILINE)
                    content = re.sub(r'__attribute__\(\(aligned\(\d+\)\)\)', '', content)
                    
                    if 'harmonized_globals.h' not in content:
                        content = '#include "harmonized_globals.h"\n' + content
                    
                    with open(path, 'w') as file: file.write(content)

    def generate_final_header(self):
        print("  [>] Pass 4: Generating Large-Model Global Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        os.makedirs(self.include_target, exist_ok=True)
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            # CRITICAL: Include stddef.h for size_t BEFORE any declarations
            f.write("/* Standard library includes */\n")
            f.write("#include <stddef.h>\n")
            f.write("#include <string.h>\n")
            f.write("#include <math.h>\n")
            f.write("#include <stdint.h>\n")
            f.write("#include <stdarg.h>\n\n")
            
            # Only forward declare struct types that are NOT already typedef'd
            if self.struct_types:
                f.write("/* Forward declarations for struct types (only those not already typedef'd) */\n")
                for struct_type in sorted(self.struct_types):
                    # Only create forward declaration if it's not already a typedef
                    if struct_type not in self.existing_typedefs:
                        f.write(f"typedef struct {struct_type} {struct_type};\n")
                f.write("\n")
            
            # Forward declare remaining struct types from type definitions
            remaining_structs = [name for name in self.type_definitions.keys() 
                               if self.type_definitions[name] == "struct" 
                               and name not in self.struct_types 
                               and name not in self.existing_typedefs]
            
            if remaining_structs:
                f.write("/* Additional struct forward declarations */\n")
                for name in sorted(remaining_structs):
                    f.write(f"struct {name};\n")
                f.write("\n")

            # Function signatures
            if self.func_signatures:
                f.write("/* Weak function declarations */\n")
                for name, sig in sorted(self.func_signatures.items()):
                    f.write(f"__attribute__((weak)) extern {sig};\n")
                f.write("\n")
            
            # Global symbols
            global_vars = [(sym, dtype) for sym, dtype in self.global_symbols.items() 
                          if sym.startswith(('D_', 'g', 'bgs', 'B_'))]
            
            if global_vars:
                f.write("/* Weak global variable declarations */\n")
                for sym, dtype in sorted(global_vars):
                    clean_type = dtype if dtype in self.type_definitions or dtype.endswith('*') else 'void'
                    # Use incomplete array syntax to resolve size mismatches in large model
                    f.write(f"__attribute__((weak)) extern {clean_type} {sym}[];\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def sync_files(self):
        for sub in ["src", "include"]:
            target = os.path.join(self.android_path, sub)
            source = os.path.join(self.decomp_path, sub)
            if os.path.exists(source):
                if os.path.exists(target): shutil.rmtree(target)
                shutil.copytree(source, target)

    def patch_cmake(self):
        print("  [>] Finalizing CMake for v8.6 Platinum...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            content = re.sub(r'# --- Harmonizer v[0-9]\.[0-9].*?# ---+', '', content, flags=re.DOTALL)
            # v8.6 Final Fix:
            # 1. -mcmodel=large : Essential to fix AArch64 relocation out of range
            # 2. -Wl,--no-rosegment : Ensures data stays in a reachable segment
            # 3. -fno-plt : Force direct addressing
            injection = (
                "\n# --- Harmonizer v8.6 Platinum Edition ---\n"
                "include_directories(include)\n"
                "add_definitions(-D__arm64__ -D_LANGUAGE_C -DN_AUDIO -DNDEBUG)\n"
                "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fcommon -w -O3 -fno-strict-aliasing -fno-plt\")\n"
                "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--allow-multiple-definition -Wl,--no-rosegment\")\n"
                "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\" \"src/*.cpp\")\n"
                "target_sources(bkawrapper PRIVATE ${ALL_C_FILES})\n"
                "target_link_libraries(bkawrapper log z m)\n"
                "# ----------------------------------------\n"
            )
            with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        print("--- Harmonizer v8.6: Platinum Edition ---")
        self.parse_typedefs()
        self.sync_files()
        self.index_all_symbols()
        self.generate_final_header()
        self.promote_and_clean()
        self.patch_cmake()
        print("--- v8.6 Complete ---")

if __name__ == "__main__":
    h = SourceHarmonizerV8_6("Android/app/src/main/cpp", "decomp-files")
    h.run()
