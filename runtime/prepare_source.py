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
        self.existing_typedefs = set()
        self.types_used_in_signatures = set()

    def sync_files(self):
        """Intelligently sync files - copy only from decomp, preserve existing Android files"""
        print("  [>] Syncing Files (preserving existing Android files)...")
        
        for sub in ["src", "include"]:
            source = os.path.join(self.decomp_path, sub)
            target = os.path.join(self.android_path, sub)
            
            if os.path.exists(source):
                # Only remove target if it exists AND is a symlink or empty
                # This prevents deleting pre-existing Android build files
                if os.path.exists(target):
                    # Check if target has critical Android files
                    has_android_files = any(
                        os.path.exists(os.path.join(target, f)) 
                        for f in ['jni', 'cpp', 'NativeBridge.cpp', 'NativeBridge.h']
                    )
                    
                    if not has_android_files:
                        # Safe to replace
                        shutil.rmtree(target)
                        shutil.copytree(source, target)
                    else:
                        # Preserve Android files, only sync decomp files
                        print(f"    Preserving existing {sub} directory with Android files")
                        # Copy decomp files WITHOUT overwriting existing ones
                        for root, dirs, files in os.walk(source):
                            rel_path = os.path.relpath(root, source)
                            target_dir = os.path.join(target, rel_path)
                            os.makedirs(target_dir, exist_ok=True)
                            
                            for file in files:
                                src_file = os.path.join(root, file)
                                dst_file = os.path.join(target_dir, file)
                                # Only copy if destination doesn't exist
                                if not os.path.exists(dst_file):
                                    shutil.copy2(src_file, dst_file)
                else:
                    # Target doesn't exist, safe to copy
                    shutil.copytree(source, target)

    def parse_typedefs(self):
        """Comprehensive typedef extraction - handles ALL C typedef patterns"""
        print("  [>] Pass 1: Global Type Discovery...")
        
        include_dir = self.include_target
        if not os.path.exists(include_dir):
            print(f"    WARNING: Include directory not found: {include_dir}")
            return
        
        # Multiple strategies to catch ALL typedef patterns
        for root, _, files in os.walk(include_dir):
            for f in files:
                if f.endswith('.h'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                    
                    # Strategy 1: Multi-line typedef blocks with braces
                    # Matches: typedef struct X { ... } TypeName;
                    typedef_block_pattern = re.compile(
                        r'typedef\s+(?:struct|union|enum)\s+\w*\s*\{[^}]*\}\s*(\w+)\s*(?://.*)?;',
                        re.DOTALL
                    )
                    for match in typedef_block_pattern.findall(content):
                        self.existing_typedefs.add(match)
                    
                    # Strategy 2: Simple typedefs (like typedef void * OSMesg;)
                    simple_typedef_pattern = re.compile(
                        r'typedef\s+(?!struct|union|enum)[\w\s\*]+\s+(\w+)\s*;'
                    )
                    for match in simple_typedef_pattern.findall(content):
                        # Avoid capturing intermediate types
                        if not match.startswith('_'):
                            self.existing_typedefs.add(match)
                    
                    # Strategy 3: Forward struct declarations (struct X;)
                    forward_pattern = re.compile(r'typedef\s+struct\s+(\w+)\s+(\w+)\s*;')
                    for struct_name, typedef_name in forward_pattern.findall(content):
                        self.existing_typedefs.add(typedef_name)
                    
                    # Strategy 4: Parse line-by-line for complex cases
                    lines = content.split('\n')
                    i = 0
                    while i < len(lines):
                        line = lines[i].strip()
                        
                        if line.startswith('typedef'):
                            # Track braces
                            brace_count = 0
                            j = i
                            typedef_text = ""
                            
                            while j < len(lines):
                                current_line = lines[j]
                                typedef_text += current_line
                                brace_count += current_line.count('{') - current_line.count('}')
                                
                                if ';' in current_line and brace_count == 0:
                                    # Extract typedef name
                                    clean_line = current_line.strip()
                                    # Remove comments
                                    clean_line = re.sub(r'//.*$', '', clean_line)
                                    clean_line = clean_line.rstrip(';').strip()
                                    
                                    if '}' in clean_line:
                                        # Get text after closing brace
                                        after_brace = clean_line.split('}')[-1].strip()
                                        words = after_brace.split()
                                        if words and words[0].isidentifier():
                                            self.existing_typedefs.add(words[0])
                                    
                                    i = j
                                    break
                                
                                j += 1
                        
                        i += 1
        
        print(f"    Found {len(self.existing_typedefs)} existing typedefs")
        # Show sample
        if self.existing_typedefs:
            sample = sorted(list(self.existing_typedefs))[:25]
            print(f"    Sample: {', '.join(sample)}")

    def index_all_symbols(self):
        """Index functions and track all types used in signatures"""
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
        
        # Extract ALL type names from parameters
        type_in_param_pat = re.compile(r'\b(?:struct\s+)?([A-Z][a-zA-Z0-9_]*)\s*\*')
        
        # Scan decomp path AND synced source
        scan_paths = [self.decomp_path, self.src_target]
        
        for base_path in scan_paths:
            if not os.path.exists(base_path):
                continue
                
            for root, _, files in os.walk(base_path):
                for f in files:
                    if f.endswith(('.c', '.h')):
                        path = os.path.join(root, f)
                        with open(path, 'r', errors='ignore') as file:
                            content = file.read()
                            
                            for full_sig, name, params in func_pat.findall(content):
                                if name not in blacklist: 
                                    clean_sig = " ".join(full_sig.replace('static ', '').split())
                                    self.func_signatures[name] = clean_sig
                                    
                                    # Extract all types from parameters
                                    for type_match in type_in_param_pat.findall(params):
                                        type_name = type_match.strip()
                                        if type_name not in {'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
                                                              'int8_t', 'int16_t', 'int32_t', 'int64_t', 
                                                              'void', 'Void', 'NULL'}:
                                            self.types_used_in_signatures.add(type_name)
                            
                            for dtype, sym in sym_pat.findall(content):
                                if sym not in blacklist: 
                                    self.global_symbols[sym] = dtype
        
        print(f"    Found {len(self.types_used_in_signatures)} types used in signatures")
        print(f"    Found {len(self.func_signatures)} function signatures")

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
                    
                    # Remove static from global scope (preserve within functions)
                    content = re.sub(r'^static\s+', '', content, flags=re.MULTILINE)
                    # Remove N64 alignment attributes
                    content = re.sub(r'__attribute__\(\(aligned\(\d+\)\)\)', '', content)
                    
                    # Add harmonized_globals.h include at the top if not present
                    if 'harmonized_globals.h' not in content:
                        content = '#include "harmonized_globals.h"\n' + content
                    
                    if content != original_content:
                        with open(path, 'w') as file: 
                            file.write(content)
                        modified += 1
        
        print(f"    Modified {modified} source files")

    def generate_final_header(self):
        """Generate harmonized_globals.h with only necessary forward declarations"""
        print("  [>] Pass 4: Generating Large-Model Global Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        os.makedirs(self.include_target, exist_ok=True)
        
        # Calculate which types need forward declarations
        types_needing_forward_decl = self.types_used_in_signatures - self.existing_typedefs
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n")
            f.write("#define HARMONIZED_GLOBALS_H\n\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            # Standard library includes
            f.write("/* Standard library includes */\n")
            f.write("#include <stddef.h>\n")
            f.write("#include <string.h>\n")
            f.write("#include <math.h>\n")
            f.write("#include <stdint.h>\n")
            f.write("#include <stdarg.h>\n\n")
            
            # Forward declarations for missing types
            if types_needing_forward_decl:
                f.write("/* Forward declarations for types not already defined */\n")
                f.write(f"/* Total: {len(types_needing_forward_decl)} types */\n")
                for type_name in sorted(types_needing_forward_decl):
                    f.write(f"typedef struct {type_name} {type_name};\n")
                f.write("\n")
            else:
                f.write("/* All types already defined - no forward declarations needed */\n\n")
            
            # Function signatures with weak linkage
            if self.func_signatures:
                f.write("/* ==== Weak Function Declarations ==== */\n")
                for name, sig in sorted(self.func_signatures.items()):
                    f.write(f"__attribute__((weak)) extern {sig};\n")
                f.write("\n")
            
            # Global variable declarations with weak linkage
            global_vars = [(sym, dtype) for sym, dtype in self.global_symbols.items() 
                          if sym.startswith(('D_', 'g', 'bgs', 'B_'))]
            
            if global_vars:
                f.write("/* ==== Weak Global Variable Declarations ==== */\n")
                for sym, dtype in sorted(global_vars):
                    clean_type = dtype if dtype.endswith('*') else 'void'
                    f.write(f"__attribute__((weak)) extern {clean_type} {sym}[];\n")
                f.write("\n")
            
            f.write("#ifdef __cplusplus\n}\n#endif\n\n")
            f.write("#endif /* HARMONIZED_GLOBALS_H */\n")
        
        print(f"    Generated harmonized_globals.h with {len(types_needing_forward_decl)} forward declarations")

    def patch_cmake(self):
        """Update CMakeLists.txt with necessary compiler flags"""
        print("  [>] Finalizing CMake for v8.7 Platinum...")
        if not os.path.exists(self.cmake_file):
            print(f"    WARNING: CMakeLists.txt not found at {self.cmake_file}")
            return
        
        with open(self.cmake_file, 'r') as f: 
            content = f.read()
        
        # Remove any previous Harmonizer injection
        content = re.sub(
            r'# --- Harmonizer v[0-9]\.[0-9].*?# ---+', 
            '', 
            content, 
            flags=re.DOTALL
        )
        
        # Inject v8.7 configuration
        injection = (
            "\n# --- Harmonizer v8.7 Platinum Edition ---\n"
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
        """Execute harmonization - ORDER IS CRITICAL"""
        print("--- Harmonizer v8.7: Platinum Edition ---")
        self.sync_files()
        self.parse_typedefs()
        self.index_all_symbols()
        self.generate_final_header()
        self.promote_and_clean()
        self.patch_cmake()
        print("--- v8.7 Complete: Ready for Android Build ---")

if __name__ == "__main__":
    h = SourceHarmonizerV8_7("Android/app/src/main/cpp", "decomp-files")
    h.run()
