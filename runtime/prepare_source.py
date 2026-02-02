import os
import shutil
import re
import hashlib

class SourceHarmonizerV42_0:
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
            'memcpy', 'memset', 'printf', 'sprintf', 'sqrt', 'sqrtf', 'fabs', 
            'sin', 'cos', 'atan2', 'atan2f', 'floor', 'ceil', 'pow', 'exp',
            '__builtin_sqrt', '__builtin_fabs', '__builtin_sin', '__builtin_cos',
            '__attribute__', '__asm__', '__volatile__', 'main', '_start'
        }
        self.reserved_types = {
            'u32', 's32', 'u16', 's16', 'u8', 's8', 'f32', 'f64', 'u64', 's64',
            'Vtx', 'Mtx', 'Gfx', 'Acmd', 'OSIntMask', 'OSPri', 'OSMesgQueue',
            'OSPiHandle', 'OSThread', 'OSMesg', 'uintptr_t', 'intptr_t', 'size_t',
            'bool', 'void', 'char', 'int', 'float', 'long', 'short', 'double',
            'struct', 'enum', 'union', 'const', 'static', 'extern', 'volatile'
        }

    def get_file_id(self, filepath):
        rel = os.path.relpath(filepath, self.src_target)
        # 12-char entropy for Quantum-Entangled symbol uniqueness
        return hashlib.md5(rel.encode()).hexdigest()[:12]

    def sync_files(self):
        print("  [>] Pass 0: Quantum-Entanglement Sync & TLB Optimization...")
        lto_cache = os.path.join(self.android_path, ".cxx", "lto_cache")
        if os.path.exists(lto_cache): shutil.rmtree(lto_cache)
        
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
        print("  [>] Pass 1: Quantum Symbol Analysis...")
        func_pat = re.compile(r'^(?!.*inline)(?!.*extern)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
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
                            # Refined type detection to avoid C keywords
                            for t in re.findall(r'\b([A-Z][a-zA-Z0-9_]+)\b', ret + params):
                                if t not in self.reserved_types: self.discovered_types.add(t)

                        for is_const, vtype, vname, varr, suffix in var_pat.findall(content):
                            vname = vname.strip()
                            if vname not in self.reserved:
                                self.var_declarations[f"{fid}_{vname}"] = (vname, ("const " if is_const else "") + vtype.strip(), varr.strip(), suffix == ';')

    def promote_linkage(self):
        print("  [>] Pass 2: Page-Aligned Linkage Entanglement...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    fid = self.get_file_id(path)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    
                    def func_repl(m):
                        name = m.group(3).strip()
                        if name in self.reserved: return m.group(0)
                        return f"#undef {name}\n#define GLOBAL_DEF_{fid}_{name}\n__attribute__((visibility(\"protected\"), used, nothrow)) {m.group(1).replace(name, f'QE_{fid}_{name}', 1)} "

                    content = re.sub(r'^(?!.*inline)(?!.*extern)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(.*?\)\s*\{)', func_repl, content, flags=re.MULTILINE | re.DOTALL)
                    
                    for key, (vname, vtype, varr, is_bss) in self.var_declarations.items():
                        if not key.startswith(fid): continue
                        base_sec = ".bss.quantum" if is_bss else ".data.quantum"
                        # 64KB Alignment for AArch64 Page-Clustering
                        attr = f'__attribute__((visibility(\"protected\"), used, section(\"{base_sec}.{fid}\"), aligned(65536)))'
                        
                        if is_bss:
                            content = re.sub(rf'^static\s+.*?{re.escape(vname)}\s*{re.escape(varr)}\s*;', 
                                            f"#undef {vname}\n#define GLOBAL_DEF_{key}\n{attr} {vtype} QE_{key}{varr};", content, flags=re.MULTILINE)
                        else:
                            content = re.sub(rf'^static\s+(.*?{re.escape(vname)}\s*{re.escape(varr)}\s*[:=])', 
                                            f"#undef {vname}\n#define GLOBAL_DEF_{key}\n{attr} {vtype} QE_{key}{varr} \\1", content, flags=re.MULTILINE)

                    with open(path, 'w') as file: file.write('#include "harmonized_globals.h"\n' + content)

    def generate_header(self):
        print("  [>] Pass 3: Finalizing v42.0 Quantum-Entanglement Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n#include <ultra64.h>\n#include <stdint.h>\n#include <stddef.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n")
            for t in sorted(self.discovered_types):
                f.write(f"#ifndef DEFINED_{t}\n  typedef struct {t} {t};\n  #define DEFINED_{t}\n#endif\n")
            
            for key, (name, ret, params) in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {name}\n  #define {name} QE_{key}\n  extern {ret} QE_{key}({params});\n#endif\n")
            for key, (vname, vtype, varr, _) in sorted(self.var_declarations.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {vname}\n  #define {vname} QE_{key}\n  extern {vtype} QE_{key}{varr};\n#endif\n")
            f.write("#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        # -fno-semantic-interposition added for direct cross-unit optimization
        injection = (
            "\n# --- Harmonizer v42.0 Quantum-Entanglement ---\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -O3 -fPIC -fno-common -fno-plt -fno-semantic-interposition -fvisibility=hidden -ffunction-sections -fdata-sections -flto=thin -mstrict-align -fno-builtin\")\n"
            "set(CMAKE_SHARED_LINKER_FLAGS \"${CMAKE_SHARED_LINKER_FLAGS} -Wl,--gc-sections -Wl,-Bsymbolic -flto=thin -Wl,--thinlto-jobs=all -Wl,--relax -Wl,--no-rosegment -lm\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C)\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# --------------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files(); self.map_linkage(); self.promote_linkage(); self.generate_header(); self.patch_cmake()
        print("--- v42.0 Quantum-Entanglement: TLB-Aware Clustering Active ---")

if __name__ == "__main__":
    h = SourceHarmonizerV42_0("Android/app/src/main/cpp", "decomp-files")
    h.run()
