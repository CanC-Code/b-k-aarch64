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
        self.global_symbols = {}
        self.func_signatures = {}
        self.existing_typedefs = set()
        self.types_used_in_signatures = set()

    def sync_files(self):
        """Copy source and include directories from decomp to Android - MUST RUN FIRST"""
        print("  [>] Syncing Files...")
        for sub in ["src", "include"]:
            target = os.path.join(self.android_path, sub)
            source = os.path.join(self.decomp_path, sub)
            if os.path.exists(source):
                if os.path.exists(target): 
                    shutil.rmtree(target)
                shutil.copytree(source, target)

    def parse_typedefs(self):
        """Extract typedef names using simple string parsing - most reliable method"""
        print("  [>] Pass 1: Global Type Discovery...")
        
        include_dir = self.include_target
        if not os.path.exists(include_dir):
            print(f"    WARNING: Include directory not found: {include_dir}")
            return
        
        for root, _, files in os.walk(include_dir):
            for f in files:
                if f.endswith('.h'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        lines = file.readlines()
                    
                    # Simple state machine to track typedef blocks
                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        
                        # Look for typedef lines
                        if line.startswith('typedef'):
                            # Track braces
                            brace_count = 0
                            typedef_started = True
                            j = i
                            
                            # Scan forward until we find the end of the typedef
                            while j < len(lines):
                                current_line = lines[j]
                                brace_count += current_line.count('{') - current_line.count('}')
                                
                                # Check if this line ends the typedef (semicolon after braces balance)
                                if ';' in current_line and brace_count == 0:
                                    # Extract the typedef name - it's the word before the semicolon
                                    # after the closing brace if present
                                    clean_line = current_line.strip()
                                    
                                    # Remove trailing semicolon and comments
                                    if '//' in clean_line:
                                        clean_line = clean_line.split('//')[0]
                                    clean_line = clean_line.rstrip(';').strip()
                                    
                                    # If there's a closing brace, get the word after it
                                    if '}' in clean_line:
                                        after_brace = clean_line.split('}')[-1].strip()
                                        # Extract the typedef name (first word)
                                        words = after_brace.split()
                                        if words:
                                            typedef_name = words[0]
                                            # Remove any trailing characters like commas
                                            typedef_name = typedef_name.strip(',*')
                                            if typedef_name and typedef_name.isidentifier():
                                                self.existing_typedefs.add(typedef_name)
                                    
                                    i = j  # Move past this typedef
                                    break
                                
                                j += 1
                        
                        i += 1
        
        print(f"    Found {len(self.existing_typedefs)} existing typedefs")
        # Debug: print first 20 typedefs found
        if self.existing_typedefs:
            sample = sorted(list(self.existing_typedefs))[:20]
            print(f"    Sample: {', '.join(sample)}")

    def index_all_symbols(self):
        """Index all functions and global symbols, tracking types used in signatures"""
        print("  [>] Pass 2: Mapping Absolute Linkage...")
        blacklist = {'main', 'memcpy', 'memset', 'memmove', 'sprintf', 'sqrt', 'sin', 'cos'}
        
        func_pat = re.compile(
            r'^(?:static\s+)?([\w\*]+\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', 
            re.MULTILINE | re.DOTALL
        )
        sym_pat = re.compile(
            r'^(?:static\s+)?([\w\*]+)\s+([a-zA-Z_]\w*)\s*[;=\[]', 
            re.MULTILINE
        )
        
        # Pattern to find type names in parameters (struct X *, TypeName *)
        type_in_param_pat = re.compile(r'\b(?:struct\s+)?([A-Z][a-zA-Z0-9_]*)\s*\*')
        
        # Scan BOTH decomp_path AND the synced src/include
        scan_paths = [self.decomp_path, self.src_target]
        
        for base_path in scan_paths:
            if not os.path.exists(base_path):
                continue
                
            for root, _, files in os.walk(base_path):
                for f in files:
                    if f.endswith(('.c', '.h')):
                        with open(os.path.join(root, f), 'r', errors='ignore') as file:
                            content = file.read()
                            
                            # Extract function signatures
                            for full_sig, name, params in func_pat.findall(content):
                                if name not in blacklist: 
                                    clean_sig = " ".join(full_sig.replace('static ', '').split())
                                    self.func_signatures[name] = clean_sig
                                    
                                    # Find all types used in this signature
                                    for type_match in type_in_param_pat.findall(params):
                                        type_name = type_match.strip()
                                        # Skip primitive types
                                        if type_name not in {'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
                                                              'int8_t', 'int16_t', 'int32_t', 'int64_t', 
                                                              'void', 'Void', 'NULL'}:
                                            self.types_used_in_signatures.add(type_name)
                            
                            # Extract global symbols
                            for dtype, sym in sym_pat.findall(content):
                                if sym not in blacklist: 
                                    self.global_symbols[sym] = dtype
        
        print(f"    Found {len(self.types_used_in_signatures)} types used in signatures")

    def promote_and_clean(self):
        """Remove static keywords and alignment attributes"""
        print("  [>] Pass 3: Breaking 4GB Address Barriers...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: 
                        content = file.read()
                    
                    # Force globalization and remove N64 alignment
                    content = re.sub(r'^static\s+', '', content, flags=re.MULTILINE)
                    content = re.sub(r'__attribute__\(\(aligned\(\d+\)\)\)', '', content)
                    
                    # Add harmonized_globals.h include at the top
                    if 'harmonized_globals.h' not in content:
                        content = '#include "harmonized_globals.h"\n' + content
                    
                    with open(path, 'w') as file: 
                        file.write(content)

    def generate_final_header(self):
        """Generate the harmonized globals header with minimal, necessary forward declarations"""
        print("  [>] Pass 4: Generating Large-Model Global Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        os.makedirs(self.include_target, exist_ok=True)
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n")
            f.write("#define HARMONIZED_GLOBALS_H\n\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            # Standard library includes (CRITICAL for size_t, etc.)
            f.write("/* Standard library includes */\n")
            f.write("#include <stddef.h>\n")
            f.write("#include <string.h>\n")
            f.write("#include <math.h>\n")
            f.write("#include <stdint.h>\n")
            f.write("#include <stdarg.h>\n\n")
            
            # Forward declare ONLY types that are:
            # 1. Used in function signatures
            # 2. NOT already typedef'd in existing headers
            types_needing_forward_decl = self.types_used_in_signatures - self.existing_typedefs
            
            if types_needing_forward_decl:
                f.write("/* Forward declarations for types used in function signatures */\n")
                f.write("/* (Only types not already typedef'd in existing headers) */\n")
                f.write(f"/* Total: {len(types_needing_forward_decl)} types */\n")
                for type_name in sorted(types_needing_forward_decl):
                    # Use opaque struct pointer pattern - safest approach
                    f.write(f"typedef struct {type_name} {type_name};\n")
                f.write("\n")
            else:
                f.write("/* No additional forward declarations needed - all types already defined */\n\n")
            
            # Function signatures (weak linkage)
            if self.func_signatures:
                f.write("/* ==== Weak Function Declarations ==== */\n")
                for name, sig in sorted(self.func_signatures.items()):
                    f.write(f"__attribute__((weak)) extern {sig};\n")
                f.write("\n")
            
            # Global variable declarations (weak linkage)
            global_vars = [(sym, dtype) for sym, dtype in self.global_symbols.items() 
                          if sym.startswith(('D_', 'g', 'bgs', 'B_'))]
            
            if global_vars:
                f.write("/* ==== Weak Global Variable Declarations ==== */\n")
                for sym, dtype in sorted(global_vars):
                    # Use incomplete array to avoid size conflicts
                    clean_type = dtype if dtype.endswith('*') else 'void'
                    f.write(f"__attribute__((weak)) extern {clean_type} {sym}[];\n")
                f.write("\n")
            
            f.write("#ifdef __cplusplus\n}\n#endif\n\n")
            f.write("#endif /* HARMONIZED_GLOBALS_H */\n")
        
        print(f"    Generated harmonized_globals.h successfully")

    def patch_cmake(self):
        """Update CMakeLists.txt with necessary compiler flags"""
        print("  [>] Finalizing CMake for v8.6 Platinum...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: 
                content = f.read()
            
            # Remove any previous Harmonizer injection
            content = re.sub(
                r'# --- Harmonizer v[0-9]\.[0-9].*?# ---+', 
                '', 
                content, 
                flags=re.DOTALL
            )
            
            # Inject v8.6 configuration
            injection = (
                "\n# --- Harmonizer v8.6 Platinum Edition ---\n"
                "# Include directories\n"
                "include_directories(include)\n"
                "include_directories(include/2.0L)\n"
                "include_directories(include/2.0L/PR)\n"
                "include_directories(include/core1)\n"
                "include_directories(include/core2)\n\n"
                
                "# Compiler definitions\n"
                "add_definitions(-D__arm64__ -D_LANGUAGE_C -DN_AUDIO -DNDEBUG)\n\n"
                
                "# Critical AArch64 compiler flags\n"
                "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fcommon -w -O3 -fno-strict-aliasing -fno-plt\")\n\n"
                
                "# Critical AArch64 linker flags\n"
                "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--allow-multiple-definition -Wl,--no-rosegment\")\n\n"
                
                "# Collect all C/C++ source files recursively\n"
                "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\" \"src/*.cpp\")\n\n"
                
                "# Add sources to target\n"
                "target_sources(bkawrapper PRIVATE ${ALL_C_FILES})\n\n"
                
                "# Link libraries\n"
                "target_link_libraries(bkawrapper log z m)\n"
                "# ----------------------------------------\n"
            )
            
            with open(self.cmake_file, 'w') as f: 
                f.write(content + injection)

    def run(self):
        """Execute the harmonization process - ORDER IS CRITICAL"""
        print("--- Harmonizer v8.6: Platinum Edition ---")
        # CRITICAL: sync_files MUST run first so parse_typedefs has files to scan
        self.sync_files()
        self.parse_typedefs()
        self.index_all_symbols()
        self.generate_final_header()
        self.promote_and_clean()
        self.patch_cmake()
        print("--- v8.6 Complete ---")

if __name__ == "__main__":
    h = SourceHarmonizerV8_6("Android/app/src/main/cpp", "decomp-files")
    h.run()
