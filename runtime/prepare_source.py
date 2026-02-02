import os
import shutil
import re
import hashlib

class SourceHarmonizerV34_0:
    def __init__(self, android_path, decomp_path):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        self.cmake_file = os.path.join(self.android_path, "CMakeLists.txt")
        self.lto_cache = os.path.join(self.android_path, ".cxx/lto_cache")
        self.func_signatures = {} 
        self.var_declarations = {} 
        self.discovered_types = set()
        self.reserved = {
            'atan2', 'atan2f', 'floor', 'floorf', 'ceil', 'ceilf', 'exp', 'log', 
            'sqrt', 'sqrtf', 'abs', 'sin', 'cos', 'tan', 'memcpy', 'memset',
            'round', 'pow', 'fabs', 'fmod', 'printf', 'sprintf', 'longjmp', 'setjmp'
        }

    def get_file_id(self, filepath):
        rel = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel.encode()).hexdigest()[:4]

    def sync_files(self):
        print("  [>] Pass 0: Singularity-X Sync & Cache Purge...")
        if os.path.exists(self.lto_cache):
            shutil.rmtree(self.lto_cache)
        
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
        print("  [>] Pass 1: Global Dependency Mapping...")
        func_pat = re.compile(r'^(?!static\s+inline)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        var_pat = re.compile(r'^static\s+(const\s+)?([\w\* ]+)\s+([a-zA-Z_]\w*)(\s*\[[^\]]*\])*\s*([:=;])', re.MULTILINE)
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    fid = self.get_file_id(path)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                        for _, ret_type, name, params in func_pat.findall(content):
                            name = name.strip()
                            if name in self.reserved: continue
                            self.func_signatures[f"{fid}_{name}"] = (name, ret_type.strip(), params.strip() or "void")
                            for t in re.findall(r'\b([A-Z][a-zA-Z0-9_]+)\b', ret_type + params):
                                self.discovered_types.add(t)

                        for is_const, vtype, vname, varr, suffix in var_pat.findall(content):
                            vname = vname.strip()
                            if vname not in self.reserved:
                                self.var_declarations[f"{fid}_{vname}"] = (vname, ("const " if is_const else "") + vtype.strip(), varr.strip(), suffix == ';')

    def promote_linkage(self):
        print("  [>] Pass 2: BSS Section Injection...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    fid = self.get_file_id(path)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                    
                    def replacer(m):
                        name = m.group(3).strip()
                        if name in self.reserved: return m.group(0)
                        promoted = m.group(0).replace('static ', '__attribute__((visibility("hidden"))) ', 1).replace(name, f"G_{fid}_{name}", 1)
                        return f"#undef {name}\n#define GLOBAL_DEF_{fid}_{name}\n{promoted}"

                    content = re.sub(r'^(?!static\s+inline)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(.*?\)\s*\{)', replacer, content, flags=re.MULTILINE | re.DOTALL)
                    
                    for key, (vname, full_type, v_arr, is_bss) in self.var_declarations.items():
                        if not key.startswith(fid): continue
                        # v34.0: Explicit sectioning to keep symbols close in memory
                        attr = '__attribute__((visibility("hidden"), aligned(16), section(".bss.harmonized")))'
                        if is_bss:
                            content = re.sub(rf'^static\s+.*?{re.escape(vname)}\s*{re.escape(v_arr)}\s*;', f"#undef {vname}\n#define GLOBAL_DEF_{key}\n{attr} {full_type} G_{key}{v_arr};", content, flags=re.MULTILINE)
                        else:
                            content = re.sub(rf'^static\s+(.*?{re.escape(vname)}\s*{re.escape(v_arr)}\s*[:=])', f"#undef {vname}\n#define GLOBAL_DEF_{key}\n{attr.replace('.bss', '.data')} {full_type} G_{key}{v_arr} \\1", content, flags=re.MULTILINE)

                    content = '#include "harmonized_globals.h"\n' + content
                    with open(path, 'w') as file: file.write(content)

    def generate_header(self):
        print("  [>] Pass 3: Generating v34 Singularity-X Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <ultra64.h>\n#include <stdint.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            for t in sorted(self.discovered_types):
                if t not in {'u32', 's32', 'f32', 'Vtx', 'Mtx', 'Gfx'}:
                    f.write(f"typedef struct {t} {t};\n")
            
            for key, (name, ret, params) in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {name}\n  #define {name} G_{key}\n")
                f.write(f"  __attribute__((visibility(\"hidden\"))) extern {ret} G_{key}({params});\n#endif\n")
            
            for key, (vname, vtype, varr, _) in sorted(self.var_declarations.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {vname}\n  #define {vname} G_{key}\n")
                f.write(f"  __attribute__((visibility(\"hidden\"))) extern {vtype} G_{key}{varr};\n#endif\n")
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        # v34.0: Removing mcmodel=large, adding linker relaxation and no-rosegment
        injection = (
            "\n# --- Harmonizer v34.0 Singularity-X ---\n"
            "include_directories(include)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -O3 -fno-common -w -fvisibility=hidden "
            "-ffunction-sections -fdata-sections -fno-plt -mstrict-align -flto=thin "
            "-fno-asynchronous-unwind-tables -fno-strict-aliasing -fno-builtin\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--gc-sections -Wl,--icf=all "
            "-Wl,-Bsymbolic -flto=thin -Wl,--thinlto-cache-dir=${CMAKE_BINARY_DIR}/lto_cache "
            "-Wl,--allow-multiple-definition -Wl,--relax -Wl,--no-rosegment -Wl,--stub-group-size=0x10000\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C)\n"
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
        print("--- v34.0 Singularity-X: BSS Injection & Cache Purge Active ---")

if __name__ == "__main__":
    h = SourceHarmonizerV34_0("Android/app/src/main/cpp", "decomp-files")
    h.run()
