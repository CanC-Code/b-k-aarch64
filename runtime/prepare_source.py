import os
import shutil
import re

class SourceHarmonizerV12_0:
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
        print("  [>] Pass 0: Hypernova Sync...")
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
        print("  [>] Pass 1: Global Indexing...")
        # Strict pattern: must be at start of line, skip inlines
        func_pat = re.compile(r'^(?!static\s+inline)static\s+([\w\*]+\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        var_pat = re.compile(r'^static\s+([\w\* ]+)\s+([a-zA-Z_]\w*)(\[[^\]]*\])?\s*[:=;]', re.MULTILINE)
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for full_sig, name, params in func_pat.findall(content):
                            sig = " ".join(full_sig.split())
                            # Better pointer erasure: keep the pointer level
                            sig = re.sub(r'[a-zA-Z_]\w*(?=\s*\*+)', 'void', sig)
                            self.func_signatures[name] = sig

                        for vtype, vname, varray in var_pat.findall(content):
                            # Preserve pointer levels for variables (e.g. void** vs void*)
                            stars = "*" * vtype.count("*")
                            clean_type = f"void{stars}" if (stars or varray) else "int"
                            self.var_declarations[vname] = clean_type

    def promote_linkage(self):
        print("  [>] Pass 2: Surgical Globalization...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                    
                    # Regex to find global static definitions and inject guard + strip
                    # This ensures we don't hit 'static' inside structs or locals
                    def replacer(m):
                        name = m.group(2)
                        full_match = m.group(0)
                        return f"#define GLOBAL_DEF_{name}\n{full_match.replace('static ', '', 1)}"

                    content = re.sub(r'^(?!static\s+inline)static\s+([\w\*]+\s+([a-zA-Z_]\w*)\s*\(.*?\)\s*\{)', 
                                    replacer, content, flags=re.MULTILINE | re.DOTALL)
                    
                    # Inject header if missing
                    if 'harmonized_globals.h' not in content:
                        content = '#include "harmonized_globals.h"\n' + content
                        
                    with open(path, 'w') as file:
                        file.write(content)

    def generate_header(self):
        print("  [>] Pass 3: Generating Final Pro-Shim...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <ultra64.h>\n#include <stdint.h>\n#include <stddef.h>\n")
            f.write("#include <stdbool.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            for name, sig in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{name}\n")
                f.write(f"__attribute__((weak, visibility(\"default\"))) extern {sig};\n")
                f.write(f"#endif\n")
            
            for name, vtype in sorted(self.var_declarations.items()):
                f.write(f"__attribute__((weak, unused)) extern {vtype} {name};\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v12.0 Hypernova ---\n"
            "include_directories(include)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -mcmodel=large -fPIC -fcommon -O3 -w -fno-builtin -fno-section-anchors\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--allow-multiple-definition -Wl,--gc-sections\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C -DFCOMMON -D_FINALROM -DGBI_BIT_DEPTH=32)\n"
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
        print("--- v12.0 Hypernova: System Stabilized ---")

if __name__ == "__main__":
    h = SourceHarmonizerV12_0("Android/app/src/main/cpp", "decomp-files")
    h.run()
