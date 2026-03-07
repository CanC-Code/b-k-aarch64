#!/usr/bin/env python3
import os
import re
import shutil
import hashlib
from typing import Set, List, Dict
from dataclasses import dataclass

@dataclass
class SymbolMapping:
    name: str
    type_info: str
    file_id: str
    is_function: bool
    params: str = ""
    section: str = ""
    is_static: bool = False
    asm_label: str = ""

class SourceHarmonizerV73_3:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")

        # C-Keywords and standard SDK types that should NEVER be forward-declared
        self.immutables = {
            'bool', 'void', 'int', 'char', 'long', 'float', 'double', 'short', 'signed', 'unsigned',
            'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64',
            'size_t', 'uintptr_t', 'intptr_t', 'Mtx', 'Gfx', 'Vtx', 'ADPCM_STATE',
            'ALMicroTime', 'ALID', 'OSMesg', 'OSThread', 'OSYieldResult', 'u_long',
            'OSPri', 'u_short', 'u_char', 'OSId', 'OSMesgQueue', 'OSIoMesg', 'OSContStatus', 'OSContPad'
        }
        
        self.c_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do', 'break', 
            'continue', 'case', 'default', 'goto', 'struct', 'union', 'enum', 'static', 
            'extern', 'const', 'volatile', 'inline', 'typedef', 'main', 'Entry'
        }

        self.conflict_registry: Set[str] = set()
        self.discovered_types: Set[str] = set()
        self.mappings: List[SymbolMapping] = []
        self.global_symbols: Dict[str, SymbolMapping] = {}
        self.all_function_names: Set[str] = set()

    def remove_comments(self, text: str) -> str:
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'//.*', '', text)
        return text

    def setup_workspace(self):
        print("[>] Pass 0: Initializing Workspace...")
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder): shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)

        for sub in ["src", "include"]:
            src, dst = os.path.join(self.decomp_path, sub), os.path.join(self.android_path, sub)
            if os.path.exists(src):
                for root, _, files in os.walk(src):
                    rel = os.path.relpath(root, src)
                    target_dir = os.path.join(dst, rel)
                    os.makedirs(target_dir, exist_ok=True)
                    for f in files: shutil.copy2(os.path.join(root, f), os.path.join(target_dir, f))

    def perform_introspection(self):
        print("[>] Pass 0.5: SDK Protection (Scanning Headers)...")
        # Pattern to find SDK functions: "extern void osStopMotor(void);"
        sdk_func_pat = re.compile(r'extern\s+[\w\* ]+\s+([A-Za-z_]\w*)\s*\(')
        patterns = [
            re.compile(r'#define\s+([A-Za-z_]\w+)'),
            re.compile(r'typedef\s+.*?\s+(\w+);'),
            re.compile(r'(?:struct|union|enum)\s+(\w+)'),
            re.compile(r'typedef\s+[\w\s\*]+\(\s*\*\s*([A-Za-z_]\w+)\s*\)')
        ]
        
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = self.remove_comments(f.read())
                        self.conflict_registry.update(sdk_func_pat.findall(content))
                        for p in patterns:
                            self.conflict_registry.update(p.findall(content))
        print(f"    [Filtered] {len(self.conflict_registry)} SDK symbols protected.")

    def harmonize_logic(self):
        print("[>] Pass 1 & 2: Weaving Linkage...")
        func_pat = re.compile(r'^(static\s+)?(([a-zA-Z_][\w\* ]{0,60}?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        data_pat = re.compile(r'^(static\s+)?([a-zA-Z_][\w\* ]{0,60}?)\s+([a-zA-Z_]\w*)\s*(?:=\s*([^;]+))?;', re.MULTILINE)

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = hashlib.md5(os.path.relpath(path, self.src_target).encode()).hexdigest()[:8]
                with open(path, 'r', errors='ignore') as file:
                    content = self.remove_comments(file.read())

                def func_repl(m):
                    is_static = m.group(1) is not None
                    ret_type = " ".join(m.group(3).split())
                    name = m.group(4).strip()
                    params = m.group(5).strip() or "void"
                    
                    if name in self.c_keywords or name in self.conflict_registry:
                        return m.group(0)

                    # Mark this name as a function so we don't typedef it as a struct later
                    self.all_function_names.add(name)

                    # Extract parameter types for forward declaration
                    for word in re.findall(r'\b([A-Z][a-zA-Z0-9_]+)\b', params + " " + ret_type):
                        if word not in self.immutables: self.discovered_types.add(word)

                    label = f"SS_{'S' if is_static else 'G'}_{fid}_{name}"
                    mapping = SymbolMapping(name, ret_type, fid, True, params, ".text", is_static, label)
                    if not is_static and name not in self.global_symbols:
                        self.global_symbols[name] = mapping
                    self.mappings.append(mapping)
                    
                    return f"\n#undef {name}\n__attribute__((used, visibility(\"protected\"))) {m.group(1) or ''}{ret_type} {name} __asm__(\"{label}\")({params}) {{"

                def data_repl(m):
                    is_static = m.group(1) is not None
                    dtype = " ".join(m.group(2).split())
                    name = m.group(3).strip()
                    value = m.group(4)

                    if name in self.c_keywords or name in self.conflict_registry or "extern" in dtype:
                        return m.group(0)

                    for word in re.findall(r'\b([A-Z][a-zA-Z0-9_]+)\b', dtype):
                        if word not in self.immutables: self.discovered_types.add(word)

                    label = f"SS_{'S' if is_static else 'G'}_{fid}_{name}"
                    mapping = SymbolMapping(name, dtype, fid, False, "", ".data", is_static, label)
                    if not is_static and name not in self.global_symbols:
                        self.global_symbols[name] = mapping
                    self.mappings.append(mapping)

                    attr = f"__attribute__((used, visibility(\"protected\")))"
                    return f"\n#undef {name}\n{attr} {m.group(1) or ''}{dtype} {name} __asm__(\"{label}\")" + (f" = {value};" if value else ";")

                patched = re.sub(func_pat, func_repl, content)
                patched = re.sub(data_pat, data_repl, patched)
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_artifacts(self):
        print("[>] Pass 3: Finalizing Artifacts...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        # FINAL GUARD: A name cannot be a Struct IF it is already a Function or SDK symbol
        final_structs = (self.discovered_types - self.all_function_names - self.conflict_registry - self.c_keywords)

        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n#include <ultra64.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")

            for t in sorted(final_structs):
                f.write(f"#if !defined({t}_DEFINED) && !defined({t})\n  typedef struct {t} {t};\n  #define {t}_DEFINED\n#endif\n")

            for name, m in self.global_symbols.items():
                f.write(f"#undef {name}\n")
                if m.is_function:
                    f.write(f"extern {m.type_info} {name}({m.params}) __asm__(\"{m.asm_label}\");\n")
                else:
                    f.write(f"extern {m.type_info} {name} __asm__(\"{m.asm_label}\");\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        self.setup_workspace()
        self.perform_introspection()
        self.harmonize_logic()
        self.generate_artifacts()
        print(f"✓ STABILIZATION COMPLETE")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV73_3("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
