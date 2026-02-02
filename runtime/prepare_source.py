import os
import shutil
import re
import hashlib

class SourceHarmonizerV35_0:
    def __init__(self, android_path, decomp_path):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        self.cmake_file = os.path.join(self.android_path, "CMakeLists.txt")
        # Store metadata for Pass 2
        self.func_signatures = {} 
        self.var_declarations = {} 
        self.discovered_types = set()
        self.reserved = {'memcpy', 'memset', 'printf', 'sprintf', 'sqrt', 'sqrtf', 'fabs', 'sin', 'cos'}

    def get_file_id(self, filepath):
        rel = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel.encode()).hexdigest()[:4]

    def sync_files(self):
        print("  [>] Pass 0: Singularity-X Clean Sync...")
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder): shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)

        for sub in ["src", "include"]:
            source = os.path.join(self.decomp_path, sub)
            target = os.path.join(self.android_path, sub)
            if not os.path.exists(source): continue
            for root, _, files in os.walk(source):
                rel = os.path.relpath(root, source)
                dest_dir = os.path.join(target, rel)
                os.makedirs(dest_dir, exist_ok=True)
                for f in files: shutil.copy2(os.path.join(root, f), os.path.join(dest_dir, f))

    def map_linkage(self):
        print("  [>] Pass 1: Global Density Mapping...")
        func_pat = re.compile(r'^(?!static\s+inline)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        var_pat = re.compile(r'^static\s+(const\s+)?([\w\* ]+)\s+([a-zA-Z_]\w*)(\s*\[[^\]]*\])*\s*([:=;])', re.MULTILINE)
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    fid = self.get_file_id(path)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                        for _, ret, name, params in func_pat.findall(content):
                            name = name.strip()
                            if name in self.reserved: continue
                            self.func_signatures[f"{fid}_{name}"] = (name, ret.strip(), params.strip() or "void")
                            for t in re.findall(r'\b([A-Z][a-zA-Z0-9_]+)\b', ret + params): self.discovered_types.add(t)

                        for is_const, vtype, vname, varr, suffix in var_pat.findall(content):
                            vname = vname.strip()
                            if vname not in self.reserved:
                                self.var_declarations[f"{fid}_{vname}"] = (vname, ("const " if is_const else "") + vtype.strip(), varr.strip(), suffix == ';')

    def promote_linkage(self):
        print("  [>] Pass 2: High-Density Section Injection...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    fid = self.get_file_id(path)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    
                    def func_repl(m):
                        name = m.group(3).strip()
                        if name in self.reserved: return m.group(0)
                        return f"#undef {name}\n#define GLOBAL_DEF_{fid}_{name}\n__attribute__((visibility(\"hidden\"))) {m.group(1).replace(name, f'G_{fid}_{name}', 1)} "

                    content = re.sub(r'^(?!static\s+inline)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(.*?\)\s*\{)', func_repl, content, flags=re.MULTILINE | re.DOTALL)
                    
                    for key, (vname, vtype, varr, is_bss) in self.var_declarations.items():
                        if not key.startswith(fid): continue
                        # Force all globals into a specific high-density section
                        attr = '__attribute__((visibility("hidden"), section(".data.harmonized")))'
                        if is_bss:
                            content = re.sub(rf'^static\s+.*?{re.escape(vname)}\s*{re.escape(v_arr)}\s*;', f"#undef {vname}\n#define GLOBAL_DEF_{key}\n{attr} {vtype} G_{key}{varr};", content, flags=re.MULTILINE)
                        else:
                            content = re.sub(rf'^static\s+(.*?{re.escape(vname)}\s*{re.escape(varr)}\s*[:=])', f"#undef {vname}\n#define GLOBAL_DEF_{key}\n{attr} {vtype} G_{key}{varr} \\1", content, flags=re.MULTILINE)

                    with open(path, 'w') as file: file.write('#include "harmonized_globals.h"\n' + content)

    def generate_header(self):
        print("  [>] Pass 3: Finalizing v35 Singularity-X Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n#include <ultra64.h>\n#ifdef __cplusplus\nextern \"C\" {\n#endif\n")
            for t in sorted(self.discovered_types):
                if t not in {'u32', 's32', 'f32', 'Vtx', 'Mtx', 'Gfx'}: f.write(f"typedef struct {t} {t};\n")
            for key, (name, ret, params) in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {name}\n  #define {name} G_{key}\n  extern {ret} G_{key}({params});\n#endif\n")
            for key, (vname, vtype, varr, _) in sorted(self.var_declarations.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {vname}\n  #define {vname} G_{key}\n  extern {vtype} G_{key}{varr};\n#endif\n")
            f.write("#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        injection = (
            "\n# --- Harmonizer v35.0 Singularity-X ---\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -O3 -fno-common -fvisibility=hidden -ffunction-sections -fdata-sections -flto=thin -mstrict-align\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--gc-sections -Wl,-Bsymbolic -flto=thin -Wl,--relax -Wl,--no-rosegment\")\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# --------------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files(); self.map_linkage(); self.promote_linkage(); self.generate_header(); self.patch_cmake()
        print("--- v35.0 Singularity-X: High-Density Relocation Model Active ---")

if __name__ == "__main__":
    h = SourceHarmonizerV35_0("Android/app/src/main/cpp", "decomp-files")
    h.run()
