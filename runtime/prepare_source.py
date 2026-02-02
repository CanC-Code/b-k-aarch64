import os
import shutil
import re

class SourceHarmonizerV10_2:
    def __init__(self, android_path, decomp_path):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        self.cmake_file = os.path.join(self.android_path, "CMakeLists.txt")
        self.func_signatures = {}
        self.var_declarations = {}
        self.primitives = {'int', 'char', 'float', 'double', 'short', 'long', 'void', 'bool',
                           's8', 'u8', 's16', 'u16', 's32', 'u32', 's64', 'u64', 'f32', 'f64', 'u32_t'}

    def sync_files(self):
        print("  [>] Pass 0: Singularity Sync...")
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
        print("  [>] Pass 1: Mapping External Surface...")
        # Matches global function definitions
        func_pat = re.compile(r'^(?:static\s+)?([\w\*]+\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        # Matches global variable definitions
        var_pat = re.compile(r'^static\s+([\w\* ]+)\s+([a-zA-Z_]\w*)(\[[^\]]*\])?\s*[:=;]', re.MULTILINE)
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        
                        for full_sig, name, params in func_pat.findall(content):
                            sig = " ".join(full_sig.replace('static ', '').split())
                            # Type erasure for non-primitives
                            words = re.findall(r'\b[a-zA-Z_]\w*\b', sig)
                            for w in set(words):
                                if w not in self.primitives and not w.endswith('_t') and w != 'struct':
                                    sig = re.sub(fr'\b{w}\s*(?=\*)', 'void ', sig)
                            self.func_signatures[name] = sig

                        for vtype, vname, varray in var_pat.findall(content):
                            # Arrays need to be handled as pointers in the extern declaration
                            clean_type = "void*" if ("*" in vtype or varray) else "int"
                            self.var_declarations[vname] = clean_type

    def promote_linkage(self):
        print("  [>] Pass 2: Surgical Scope Promotion...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                    
                    # Instead of deleting static, replace it with nothing 
                    # only at the start of declarations to avoid breaking 'static inline'
                    content = re.sub(r'^(static\s+)(?!inline)', '', content, flags=re.MULTILINE)
                    
                    # Inject shim include after system includes
                    if 'harmonized_globals.h' not in content:
                        # Find the last #include and put ours under it
                        inc_match = list(re.finditer(r'#include\s+.*?\n', content))
                        if inc_match:
                            pos = inc_match[-1].end()
                            content = content[:pos] + '\n#include "harmonized_globals.h"\n' + content[pos:]
                        else:
                            content = '#include "harmonized_globals.h"\n' + content
                        
                    with open(path, 'w') as file:
                        file.write(content)

    def generate_header(self):
        print("  [>] Pass 3: Generating Singularity Shim...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <ultra64.h>\n#include <stdint.h>\n#include <stddef.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            f.write("/* Globally Promoted Functions */\n")
            for name, sig in sorted(self.func_signatures.items()):
                f.write(f"__attribute__((weak, visibility(\"default\"))) extern {sig};\n")
            
            f.write("\n/* Globally Promoted Variables */\n")
            for name, vtype in sorted(self.var_declarations.items()):
                f.write(f"__attribute__((weak)) extern {vtype} {name};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v10.2 Singularity ---\n"
            "include_directories(include)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fcommon -O3 -w -fno-builtin -ffunction-sections -fdata-sections\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--allow-multiple-definition -Wl,--gc-sections\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C -DFCOMMON)\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# ------------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files()
        self.map_linkage()
        self.promote_linkage()
        self.generate_header()
        self.patch_cmake()
        print("--- v10.2 Singularity: Deployment Ready ---")

if __name__ == "__main__":
    h = SourceHarmonizerV10_2("Android/app/src/main/cpp", "decomp-files")
    h.run()
