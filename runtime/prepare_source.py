import os
import shutil
import re

class SourceHarmonizerV15_1:
    def __init__(self, android_path, decomp_path):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        self.cmake_file = os.path.join(self.android_path, "CMakeLists.txt")
        self.func_signatures = {}
        self.var_declarations = {}
        self.discovered_types = set()

    def sync_files(self):
        print("  [>] Pass 0: Nova Syncing...")
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
        print("  [>] Pass 1: Semantic Linkage Indexing...")
        # v15.1: Stabilized capture groups
        func_pat = re.compile(r'^(?!static\s+inline)static\s+(([\w\* ]+)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        var_pat = re.compile(r'^static\s+([\w\* ]+)\s+([a-zA-Z_]\w*)(\[[^\]]*\])?\s*[:=;]', re.MULTILINE)
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for _, ret_type, name, params in func_pat.findall(content):
                            clean_ret = ret_type.strip()
                            clean_params = params.strip() if params.strip() else "void"
                            self.func_signatures[name] = (clean_ret, clean_params)
                            for t in re.findall(r'([A-Z]\w+)', clean_ret + clean_params):
                                self.discovered_types.add(t)

                        for vtype, vname, _ in var_pat.findall(content):
                            self.var_declarations[vname] = vtype.strip()

    def promote_linkage(self):
        print("  [>] Pass 2: Definitive Symbol Promotion...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                    
                    # v15.1: Corrected group indexing for re.sub
                    def replacer(m):
                        # Group 1: Full Sig, Group 2: Return Type, Group 3: Name
                        name = m.group(3)
                        promoted = m.group(0).replace('static ', '', 1).replace(name, f"G_{name}", 1)
                        return f"#define GLOBAL_DEF_{name}\n{promoted}"

                    # Updated regex pattern to match the findall() structure in map_linkage
                    pattern = r'^(?!static\s+inline)static\s+(([\w\* ]+)\s+([a-zA-Z_]\w*)\s*\(.*?\)\s*\{)'
                    content = re.sub(pattern, replacer, content, flags=re.MULTILINE | re.DOTALL)
                    
                    if 'harmonized_globals.h' not in content:
                        content = '#include "harmonized_globals.h"\n' + content
                        
                    with open(path, 'w') as file:
                        file.write(content)

    def generate_header(self):
        print("  [>] Pass 3: Generating v15.1 Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <ultra64.h>\n#include <stdint.h>\n#include <stddef.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            for t in sorted(self.discovered_types):
                if t not in ['Vtx', 'Mtx', 'u32', 's32', 'u64', 's64', 'f32', 'f64']:
                    f.write(f"typedef struct {t} {t};\n")
            
            for name, (ret, params) in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{name}\n")
                f.write(f"  #define {name} G_{name}\n")
                f.write(f"  __attribute__((weak)) extern {ret} G_{name}({params});\n")
                f.write(f"#endif\n")
            
            for name, vtype in sorted(self.var_declarations.items()):
                f.write(f"#ifndef GLOBAL_DEF_{name}\n")
                f.write(f"  #define {name} G_{name}\n")
                f.write(f"#endif\n")
                f.write(f"__attribute__((weak, common)) extern {vtype} G_{name};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v15.1 Nova-Event ---\n"
            "include_directories(include)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fPIC -fcommon -O3 -flto -w -fno-plt -fvisibility=hidden\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -flto -Wl,--allow-multiple-definition -Wl,--no-relax\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C -DGBI_BIT_DEPTH=32)\n"
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
        print("--- v15.1 Nova-Event: System Stabilized ---")

if __name__ == "__main__":
    h = SourceHarmonizerV15_1("Android/app/src/main/cpp", "decomp-files")
    h.run()
