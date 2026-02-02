import os
import shutil
import re

class SourceHarmonizerV10_0:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")
        self.func_signatures = {}
        # Primitives we allow to remain in signatures
        self.primitives = {'int', 'char', 'float', 'double', 'short', 'long', 'void', 'bool',
                           's8', 'u8', 's16', 'u16', 's32', 'u32', 's64', 'u64', 'f32', 'f64'}

    def sync_files(self):
        print("  [>] Pass 0: Syncing...")
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
                    shutil.copy2(os.path.join(root, f), os.path.join(dest_dir, f))

    def map_linkage(self):
        print("  [>] Pass 1: Symbol Shim Mapping...")
        # Matches global function definitions
        func_pat = re.compile(r'^(?:static\s+)?([\w\*]+\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for full_sig, name, params in func_pat.findall(content):
                            # The 'Omega' Trick: 
                            # Convert any non-primitive pointer to void* in the global header.
                            # This bypasses ALL 'unknown type' and 'conflicting type' errors.
                            sig = " ".join(full_sig.replace('static ', '').split())
                            
                            # Replace custom types followed by '*' with 'void '
                            # Matches 'BKModel *' -> 'void *'
                            # Matches 'BKVtxRef *' -> 'void *'
                            # It leaves 'int *' or 'void *' alone.
                            words = re.findall(r'\b[a-zA-Z_]\w*\b', sig)
                            for w in set(words):
                                if w not in self.primitives and not w.endswith('_t') and w != 'struct':
                                    sig = re.sub(fr'\b{w}\s*(?=\*)', 'void ', sig)
                            
                            self.func_signatures[name] = sig

    def promote_linkage(self):
        print("  [>] Pass 2: Globalization...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        lines = file.readlines()
                    
                    output = [re.sub(r'^static\s+', '', line) for line in lines]
                    # Append header at the bottom as a fallback
                    output.append('\n#include "harmonized_globals.h"\n')
                        
                    with open(path, 'w') as file:
                        file.writelines(output)

    def generate_header(self):
        print("  [>] Pass 3: Generating Omega fallback header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <ultra64.h>\n#include <stdint.h>\n#include <stddef.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            for name, sig in sorted(self.func_signatures.items()):
                # Visibility default ensures the symbols are exported in the .so
                # Weak ensures we don't crash if the real header is included later
                f.write(f"__attribute__((weak, visibility(\"default\"))) extern {sig};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v10.0 Omega ---\n"
            "include_directories(include)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fcommon -O3 -w\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--allow-multiple-definition\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C -DFCOMMON)\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# ------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files()
        self.map_linkage()
        self.promote_linkage()
        self.generate_header()
        self.patch_cmake()
        print("--- v10.0 Omega Link: Complete ---")

if __name__ == "__main__":
    h = SourceHarmonizerV10_0("Android/app/src/main/cpp", "decomp-files")
    h.run()
