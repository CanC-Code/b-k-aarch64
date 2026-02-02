import os
import shutil
import re

class SourceHarmonizerV16_0:
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
        print("  [>] Pass 0: Pulsar-Prime Sync...")
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
        print("  [>] Pass 1: Semantic Indexing...")
        # v16.0: Enhanced regex to handle multi-line signatures and complex pointers
        func_pat = re.compile(r'^(?!static\s+inline)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        var_pat = re.compile(r'^static\s+([\w\* ]+)\s+([a-zA-Z_]\w*)(\[[^\]]*\])?\s*[:=;]', re.MULTILINE)
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for _, ret_type, name, params in func_pat.findall(content):
                            clean_ret = " ".join(ret_type.split())
                            clean_params = " ".join(params.split()) if params.strip() else "void"
                            self.func_signatures[name] = (clean_ret, clean_params)
                            
                            # Type Discovery for forward declarations
                            for t in re.findall(r'\b([A-Z][a-zA-Z0-9_]+)\b', clean_ret + clean_params):
                                self.discovered_types.add(t)

                        for vtype, vname, _ in var_pat.findall(content):
                            self.var_declarations[vname] = vtype.strip()

    def promote_linkage(self):
        print("  [>] Pass 2: Globalization & Namespace Injection...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                    
                    def replacer(m):
                        name = m.group(3)
                        # v16.0: Using __attribute__((visibility("hidden"))) to save PLT slots
                        promoted = m.group(0).replace('static ', '', 1).replace(name, f"G_{name}", 1)
                        return f"#define GLOBAL_DEF_{name}\n{promoted}"

                    pattern = r'^(?!static\s+inline)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(.*?\)\s*\{)'
                    content = re.sub(pattern, replacer, content, flags=re.MULTILINE | re.DOTALL)
                    
                    if 'harmonized_globals.h' not in content:
                        content = '#include "harmonized_globals.h"\n' + content
                        
                    with open(path, 'w') as file:
                        file.write(content)

    def generate_header(self):
        print("  [>] Pass 3: Generating Optimized v16 Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <ultra64.h>\n#include <stdint.h>\n#include <stddef.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            f.write("/* Opaque Type Forwarding */\n")
            for t in sorted(self.discovered_types):
                if t not in ['Vtx', 'Mtx', 'u32', 's32', 'u64', 's64', 'f32', 'f64', 'Addr']:
                    f.write(f"typedef struct {t} {t};\n")
            
            f.write("\n/* Namespaced Linkage */\n")
            for name, (ret, params) in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{name}\n")
                f.write(f"  #define {name} G_{name}\n")
                # v16.0: Weak + Hidden ensures no cross-library bloat
                f.write(f"  __attribute__((weak, visibility(\"hidden\"))) extern {ret} G_{name}({params});\n")
                f.write(f"#endif\n")
            
            for name, vtype in sorted(self.var_declarations.items()):
                f.write(f"#ifndef GLOBAL_DEF_{name}\n")
                f.write(f"  #define {name} G_{name}\n")
                f.write(f"#endif\n")
                f.write(f"__attribute__((weak, common, visibility(\"hidden\"))) extern {vtype} G_{name};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        # v16.0: High-performance Linker Flags
        injection = (
            "\n# --- Harmonizer v16.0 Pulsar-Prime ---\n"
            "include_directories(include)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fPIC -fcommon -O3 -flto -w "
            "-ffunction-sections -fdata-sections -fno-plt -fvisibility=hidden\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -flto -Wl,--gc-sections -s "
            "-Wl,--allow-multiple-definition -Wl,--no-relax\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C -DGBI_BIT_DEPTH=32)\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# --------------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files()
        self.map_linkage()
        self.promote_linkage()
        self.generate_header()
        self.patch_cmake()
        print("--- v16.0 Pulsar-Prime: Linker Pressure Stabilized ---")

if __name__ == "__main__":
    h = SourceHarmonizerV16_0("Android/app/src/main/cpp", "decomp-files")
    h.run()
