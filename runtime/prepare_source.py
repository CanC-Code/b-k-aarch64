import os
import shutil
import re

class SourceHarmonizerV8_9:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")
        self.existing_types = set()
        self.func_signatures = {}
        self.types_used_in_signatures = set()

    def sync_files(self):
        print("  [>] Pass 0: Syncing & Preserving...")
        for sub in ["src", "include"]:
            source = os.path.join(self.decomp_path, sub)
            target = os.path.join(self.android_path, sub)
            if not os.path.exists(source): continue
            
            os.makedirs(target, exist_ok=True)
            for root, _, files in os.walk(source):
                rel = os.path.relpath(root, source)
                dest_dir = os.path.join(target, rel)
                os.makedirs(dest_dir, exist_ok=True)
                for f in files:
                    dest_file = os.path.join(dest_dir, f)
                    if not os.path.exists(dest_file):
                        shutil.copy2(os.path.join(root, f), dest_file)

    def parse_definitions(self):
        """Build a comprehensive index of types we MUST NOT forward-declare"""
        print("  [>] Pass 1: Recursive Type Discovery...")
        
        # 1. Start with hardcoded primitives
        self.existing_types.update([
            's8', 'u8', 's16', 'u16', 's32', 'u32', 's64', 'u64', 
            'f32', 'f64', 'bool', 'size_t', 'uintptr_t', 'intptr_t',
            'void', 'int', 'float', 'char', 'double', 'short', 'long'
        ])
        
        # 2. Dynamic regex for typedefs and structs
        patterns = [
            re.compile(r'typedef\s+(?:struct|union|enum)?\s*[\w\s\*]+\s+([a-zA-Z_]\w*)\s*;'),
            re.compile(r'}\s*([a-zA-Z_]\w*)\s*;'),
            re.compile(r'(?:struct|union|enum)\s+([a-zA-Z_]\w*)\s*\{')
        ]

        # Scan every header in the include path
        for root, _, files in os.walk(self.include_target):
            for f in files:
                if f.endswith('.h'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for pat in patterns:
                            self.existing_types.update(pat.findall(content))
        
        print(f"    Indexed {len(self.existing_types)} existing types (Protected).")

    def map_linkage(self):
        """Extract signatures while identifying types that are genuinely missing"""
        print("  [>] Pass 2: Linkage Mapping...")
        # Matches: static void func(Type *ptr) {
        func_pat = re.compile(r'^(?:static\s+)?([\w\*]+\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        type_in_param_pat = re.compile(r'\b([a-zA-Z_]\w*)\s*\*')
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for full_sig, name, params in func_pat.findall(content):
                            # Sanitize: Remove static, collapse newlines
                            clean_sig = " ".join(full_sig.replace('static ', '').split())
                            self.func_signatures[name] = clean_sig
                            
                            # Log types used as pointers
                            for t_name in type_in_param_pat.findall(params):
                                if t_name not in self.existing_types:
                                    self.types_used_in_signatures.add(t_name)

    def harmonize_sources(self):
        """Pass 3: Strip static and inject header SAFELY"""
        print("  [>] Pass 3: Global Linkage Promotion...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        lines = file.readlines()
                    
                    new_lines = []
                    header_injected = False
                    for line in lines:
                        # Strip static from function starts and global variables
                        processed = re.sub(r'^static\s+', '', line)
                        
                        # Perfect Injection: Wait until after ultra64.h or first include
                        if not header_injected and '#include' in line:
                            new_lines.append(processed)
                            new_lines.append('#include "harmonized_globals.h"\n')
                            header_injected = True
                        else:
                            new_lines.append(processed)
                    
                    # Fallback if no includes found
                    if not header_injected:
                        new_lines.insert(0, '#include "harmonized_globals.h"\n')

                    with open(path, 'w') as file:
                        file.writelines(new_lines)

    def generate_header(self):
        """Pass 4: Create the final conflict-free header"""
        print("  [>] Pass 4: Generating Master Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            # Forward Declarations
            if self.types_used_in_signatures:
                f.write("/* Forward Declarations */\n")
                for t in sorted(self.types_used_in_signatures):
                    f.write(f"struct {t};\ntypedef struct {t} {t};\n")
            
            # Function Prototypes
            f.write("\n/* Globally Promoted Functions */\n")
            for name, sig in sorted(self.func_signatures.items()):
                # Weak attribute allows us to bypass 'multiple definition' linker errors
                f.write(f"__attribute__((weak)) extern {sig};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        
        # Remove old harmonizer blocks
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v8.9 Platinum Edition ---\n"
            "include_directories(include)\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fcommon -w -O3\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--allow-multiple-definition\")\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# ----------------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files()
        self.parse_definitions()
        self.map_linkage()
        self.harmonize_sources()
        self.generate_header()
        self.patch_cmake()
        print("--- Harmonization Complete: v8.9 Platinum ---")

if __name__ == "__main__":
    h = SourceHarmonizerV8_9("Android/app/src/main/cpp", "decomp-files")
    h.run()
