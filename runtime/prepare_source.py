import os
import shutil
import re
import hashlib

class SourceHarmonizerV46_0:
    def __init__(self, android_path, decomp_path):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        self.cmake_file = os.path.join(self.android_path, "CMakeLists.txt")
        self.func_signatures = {} 
        self.var_declarations = {} 
        self.discovered_types = set()
        
        # Expanded to include internal SDK struct suffixes (_s) to prevent "struct ALSeq vs struct ALSeq_s" errors
        self.reserved_types = {
            'u32', 's32', 'u16', 's16', 'u8', 's8', 'f32', 'f64', 'u64', 's64',
            'Vtx', 'Mtx', 'Gfx', 'Acmd', 'OSIntMask', 'OSPri', 'OSMesgQueue',
            'OSPiHandle', 'OSThread', 'OSMesg', 'uintptr_t', 'intptr_t', 'size_t',
            'bool', 'void', 'char', 'int', 'float', 'long', 'short', 'double',
            'struct', 'enum', 'union', 'const', 'static', 'extern', 'volatile',
            'ALCSPlayer', 'ALSeq', 'ALEvent', 'ALEventListItem', 'ALEventQueue',
            'ALPlayer', 'ALSeqpConfig', 'ALSynConfig', 'ALVoiceConfig', 'ALInstrument',
            'ALBank', 'ALWave', 'ALEnvelope', 'ALKeyMap', 'ALInstrumentListItem',
            'ALBankFile', 'ALVoice', 'ALSndpConfig', 'ALSndPlayer', 'ALSeqPlayer',
            'ALSeq_s', 'ALCSPlayer_s', 'ALInstrument_s', 'ALBank_s', 'ALVoice_s'
        }
        
        self.reserved_names = {
            'memcpy', 'memset', 'printf', 'sprintf', 'sqrt', 'sqrtf', 'fabs', 
            'sin', 'cos', 'atan2', 'atan2f', 'floor', 'ceil', 'pow', 'exp',
            'main', '_start', '__builtin_sqrt', '__attribute__', '__asm__'
        }

    def get_file_id(self, filepath):
        rel = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel.encode()).hexdigest()[:12]

    def sync_files(self):
        print("  [>] Pass 0: Nebula-Link Sync...")
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
        print("  [>] Pass 1: Recursive Type Validation...")
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
                            if name in self.reserved_names: continue
                            self.func_signatures[f"{fid}_{name}"] = (name, ret.strip(), params.strip() or "void")
                            
                            for t in re.findall(r'\b([A-Z][a-zA-Z0-9_]*)\b', ret + params):
                                if t not in self.reserved_types:
                                    self.discovered_types.add(t)

                        for is_const, vtype, vname, varr, suffix in var_pat.findall(content):
                            vname = vname.strip()
                            if vname not in self.reserved_names:
                                self.var_declarations[f"{fid}_{vname}"] = (vname, ("const " if is_const else "") + vtype.strip(), varr.strip(), suffix == ';')

    def promote_linkage(self):
        print("  [>] Pass 2: Nebula-Link Visibility Promotion...")
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    fid = self.get_file_id(path)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    
                    def func_repl(m):
                        name = m.group(3).strip()
                        if name in self.reserved_names: return m.group(0)
                        return f"#undef {name}\n#define GLOBAL_DEF_{fid}_{name}\n__attribute__((visibility(\"protected\"), used)) {m.group(1).replace(name, f'NL_{fid}_{name}', 1)} "

                    content = re.sub(r'^(?!.*inline)(?!.*extern)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(.*?\)\s*\{)', func_repl, content, flags=re.MULTILINE | re.DOTALL)
                    
                    for key, (vname, vtype, varr, is_bss) in self.var_declarations.items():
                        if not key.startswith(fid): continue
                        attr = f'__attribute__((visibility(\"protected\"), used, aligned(8)))'
                        if is_bss:
                            content = re.sub(rf'^static\s+.*?{re.escape(vname)}\s*{re.escape(varr)}\s*;', 
                                            f"#undef {vname}\n#define GLOBAL_DEF_{key}\n{attr} {vtype} NL_{key}{varr};", content, flags=re.MULTILINE)
                        else:
                            content = re.sub(rf'^static\s+(.*?{re.escape(vname)}\s*{re.escape(varr)}\s*[:=])', 
                                            f"#undef {vname}\n#define GLOBAL_DEF_{key}\n{attr} {vtype} NL_{key}{varr} \\1", content, flags=re.MULTILINE)

                    with open(path, 'w') as file: file.write('#include "harmonized_globals.h"\n' + content)

    def generate_header(self):
        print("  [>] Pass 3: Finalizing v46.0 Nebula-Link Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            # Force SDK headers OUTSIDE of extern "C" for better type resolution
            f.write("#include <ultra64.h>\n#include <stdbool.h>\n#include <stdint.h>\n#include <stddef.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n")
            
            for t in sorted(self.discovered_types):
                # Using more defensive guards to prevent ALSeq-style redefinitions
                f.write(f"#ifndef DEFINED_{t}\n  #ifndef {t}_defined\n    typedef struct {t} {t};\n    #define {t}_defined\n  #endif\n  #define DEFINED_{t}\n#endif\n")
            
            for key, (name, ret, params) in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {name}\n  #define {name} NL_{key}\n  extern {ret} NL_{key}({params});\n#endif\n")
            for key, (vname, vtype, varr, _) in sorted(self.var_declarations.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {vname}\n  #define {vname} NL_{key}\n  extern {vtype} NL_{key}{varr};\n#endif\n")
            f.write("#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def patch_cmake(self):
        if not os.path.exists(self.cmake_file): return
        with open(self.cmake_file, 'r') as f: content = f.read()
        content = re.sub(r'# --- Harmonizer.*?# ---+', '', content, flags=re.DOTALL)
        injection = (
            "\n# --- Harmonizer v46.0 Nebula-Link ---\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -O3 -fPIC -fno-common -fvisibility=hidden -ffunction-sections -fdata-sections -flto=thin\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C)\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# --------------------------------------\n"
        )
        with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        self.sync_files(); self.map_linkage(); self.promote_linkage(); self.generate_header(); self.patch_cmake()
        print("--- v46.0 Nebula-Link: Defensive Type Guarding Active ---")

if __name__ == "__main__":
    h = SourceHarmonizerV46_0("Android/app/src/main/cpp", "decomp-files")
    h.run()
