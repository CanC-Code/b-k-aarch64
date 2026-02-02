import os
import shutil
import re
import hashlib

class SourceHarmonizerV33_0:
    def __init__(self, android_path, decomp_path):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        self.cmake_file = os.path.join(self.android_path, "CMakeLists.txt")
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
        print("  [>] Pass 0: Quasar Sync...")
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
        print("  [>] Pass 1: Semantic Structural Analysis...")
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
                            if name.strip() in self.reserved: continue
                            self.func_signatures[f"{fid}_{name.strip()}"] = (name.strip(), re.sub(r'\s+', ' ', ret_type.strip()), re.sub(r'\s+', ' ', params.strip()) if params.strip() else "void")
                            for t in re.findall(r'\b([A-Z][a-zA-Z0-9_]+)\b', ret_type + params):
                                self.discovered_types.add(t)

                        for is_const, vtype, vname, varr, suffix in var_pat.findall(content):
                            if vname.strip() not in self.reserved:
                                self.var_declarations[f"{fid}_{vname.strip()}"] = (vname.strip(), ("const " if is_const else "") + vtype.strip(), varr.strip(), suffix == ';')

    def promote_linkage(self):
        print("  [>] Pass 2: Quasar Visibility & Alignment...")
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
                        prefix = '__attribute__((visibility("hidden"), aligned(32))) '
                        if is_bss:
                            content = re.sub(rf'^static\s+.*?{re.escape(vname)}\s*{re.escape(v_arr)}\s*;', f"#undef {vname}\n#define GLOBAL_DEF_{key}\n{prefix}{full_type} G_{key}{v_arr} = {{0}};", content, flags=re.MULTILINE)
                        else:
                            content = re.sub(rf'^static\s+(.*?{re.escape(vname)}\s*{re.escape(v_arr)}\s*[:=])', f"#undef {vname}\n#define GLOBAL_DEF_{key}\n{prefix}{full_type} G_{key}{v_arr} \\1", content, flags=re.MULTILINE)

                    content = '#include "harmonized_globals.h"\n' + content
                    with open(path, 'w') as file: file.write(content)

    def generate_header(self):
        print("  [>] Pass 3: Generating v33 Quasar Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <math.h>\n#include <string.h>\n#include <ultra64.h>\n#include <stdint.h>\n#include <stddef.h>\n")
            f.write("#pragma pack(push, 16)\n#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            for t in sorted(self.discovered_types):
                if t not in {'u32', 's32', 'f32', 'Vtx', 'Mtx', 'Gfx', 'u64', 's64'}:
                    f.write(f"#ifndef DEFINED_{t}\n  typedef struct {t} {t};\n  #define DEFINED_{t}\n#endif\n")
            
            for key, (name, ret, params) in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {name}\n  #define {name} G_{key}\n")
                f.write(f"  __attribute__((visibility(\"hidden\"))) extern {ret} G_{key}({params});\n#endif\n")
            
            for key, (vname, vtype, varr, _) in sorted(self.var_declarations.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {vname}\n  #define {vname} G_{key}\n")
                f.write(f"  __attribute__((visibility(\"hidden\"), aligned(32))) extern {vtype} G_{key}{varr};\n#endif\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#pragma pack(pop)\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        
        # v33.0: Forcing Single-Partition LTO and strict alignment anchoring
        injection = (
            "\n# --- Harmonizer v33.0 Quasar ---\n"
            "include_directories(include)\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -O3 -fPIC -fno-common -w -fvisibility=hidden "
            "-ffunction-sections -fdata-sections -falign-functions=32 -falign-loops=32 "
            "-fno-plt -mstrict-align -flto=thin -mcmodel=large -fno-jump-tables "
            "-fmerge-all-constants -fno-asynchronous-unwind-tables -fno-strict-aliasing "
            "-fno-builtin -fsection-anchors\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--gc-sections -Wl,--icf=all -s "
            "-Wl,-Bsymbolic -Wl,--fix-cortex-a53-843419 -Wl,--fix-cortex-a53-835769 -Wl,--hash-style=gnu "
            "-flto=thin -Wl,--thinlto-cache-dir=${CMAKE_BINARY_DIR}/lto_cache -Wl,--allow-multiple-definition "
            "-Wl,--no-relax -Wl,--exclude-libs,ALL -Wl,--stub-group-size=0x100000 -Wl,-z,relro -Wl,-z,now "
            "-Wl,--plugin-opt=-import-instr-limit=100 -Wl,--plugin-opt=-lto-partitions=1\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C -DGBI_BIT_DEPTH=32)\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# -------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files()
        self.map_linkage()
        self.promote_linkage()
        self.generate_header()
        self.patch_cmake()
        print("--- v33.0 Quasar: Struct Padding & LTO Partitioning Fixed ---")

if __name__ == "__main__":
    h = SourceHarmonizerV33_0("Android/app/src/main/cpp", "decomp-files")
    h.run()
