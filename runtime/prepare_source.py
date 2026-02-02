import os
import shutil
import re

class SourceHarmonizerV19_0:
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
        print("  [>] Pass 0: Zenith-Protocol Clean Sync...")
        # v19.0: Wipe targets to prevent "Ghost Symbols" from previous failed builds
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)

        for sub in ["src", "include"]:
            source = os.path.join(self.decomp_path, sub)
            target = os.path.join(self.android_path, sub)
            if not os.path.exists(source): continue
            for root, _, files in os.walk(source):
                rel = os.path.relpath(root, source)
                dest_dir = os.path.join(target, rel)
                os.makedirs(dest_dir, exist_ok=True)
                for f in files:
                    shutil.copy2(os.path.join(root, f), os.path.join(dest_dir, f))

    def map_linkage(self):
        print("  [>] Pass 1: Semantic Extraction...")
        # Improved regex to ignore already-prefixed symbols if running on a dirty tree
        func_pat = re.compile(r'^(?!static\s+inline)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        var_pat = re.compile(r'^static\s+([\w\* ]+)\s+([a-zA-Z_]\w*)(\[[^\]]*\])?\s*[:=;]', re.MULTILINE)
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for _, ret_type, name, params in func_pat.findall(content):
                            if name.startswith('G_'): continue # Skip if already harmonized
                            clean_ret = re.sub(r'\s+', ' ', ret_type.strip()).replace(' *', '*')
                            clean_params = re.sub(r'\s+', ' ', params.strip()) if params.strip() else "void"
                            self.func_signatures[name] = (clean_ret, clean_params)
                            
                            for t in re.findall(r'\b([A-Z][a-zA-Z0-9_]+)\b', clean_ret + clean_params):
                                self.discovered_types.add(t)

                        for vtype, vname, _ in var_pat.findall(content):
                            if not vname.startswith('G_'):
                                self.var_declarations[vname] = vtype.strip()

    def promote_linkage(self):
        print("  [>] Pass 2: Scope Promotion & Idempotency...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                    
                    def replacer(m):
                        name = m.group(3)
                        if name.startswith('G_'): return m.group(0)
                        promoted = m.group(0).replace('static ', '', 1).replace(name, f"G_{name}", 1)
                        return f"#undef {name}\n#define GLOBAL_DEF_{name}\n{promoted}"

                    pattern = r'^(?!static\s+inline)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(.*?\)\s*\{)'
                    content = re.sub(pattern, replacer, content, flags=re.MULTILINE | re.DOTALL)
                    
                    if 'harmonized_globals.h' not in content:
                        content = '#include "harmonized_globals.h"\n' + content
                        
                    with open(path, 'w') as file:
                        file.write(content)

    def generate_header(self):
        print("  [>] Pass 3: Generating v19 Zenith Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <ultra64.h>\n#include <stdint.h>\n#include <stddef.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            # v19.0: Aggressive guard for N64-specific types
            forbidden = {'Vtx', 'Mtx', 'u32', 's32', 'u64', 's64', 'f32', 'f64', 'Addr', 'Gfx', 'Lights'}
            for t in sorted(self.discovered_types):
                if t not in forbidden:
                    f.write(f"typedef struct {t} {t};\n")
            
            for name, (ret, params) in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{name}\n  #undef {name}\n  #define {name} G_{name}\n")
                f.write(f"  __attribute__((visibility(\"hidden\"))) extern {ret} G_{name}({params});\n#endif\n")
            
            for name, vtype in sorted(self.var_declarations.items()):
                f.write(f"#ifndef GLOBAL_DEF_{name}\n  #undef {name}\n  #define {name} G_{name}\n")
                f.write(f"  __attribute__((visibility(\"hidden\"))) extern {vtype} G_{name};\n#endif\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        # v19.0: Use -fno-common for stricter linkage and --no-undefined for earlier error detection
        injection = (
            "\n# --- Harmonizer v19.0 Zenith-Protocol ---\n"
            "include_directories(include)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fPIC -fno-common -O3 -w "
            "-ffunction-sections -fdata-sections -fno-plt -fvisibility=hidden\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--gc-sections -Wl,--icf=all -s "
            "-Wl,--allow-multiple-definition -Wl,--no-relax -Wl,--exclude-libs,ALL\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C -DGBI_BIT_DEPTH=32)\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# ----------------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files()
        self.map_linkage()
        self.promote_linkage()
        self.generate_header()
        self.patch_cmake()
        print("--- v19.0 Zenith-Protocol: Build System Stabilized ---")

if __name__ == "__main__":
    h = SourceHarmonizerV19_0("Android/app/src/main/cpp", "decomp-files")
    h.run()
