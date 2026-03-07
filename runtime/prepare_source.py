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
    params: str = ""
    asm_label: str = ""

class SourceHarmonizerV74_1:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")

        self.blacklisted_types = {'NULL', 'TRUE', 'FALSE', 'static', 'inline', 'extern', 'void'}
        self.sdk_types = {
            'ALBank', 'ALSeq', 'ALInstrument', 'ALHeap', 'OSMesg', 'OSThread', 
            'OSMesgQueue', 'Gfx', 'Mtx', 'Vtx', 'u8', 'u16', 'u32', 'u64', 
            's8', 's16', 's32', 's64', 'f32', 'f64', 'Vp', 'Light'
        }
        
        self.discovered_structs: Set[str] = set()
        self.global_symbols: Dict[str, SymbolMapping] = {}

    def is_custom_struct(self, name: str) -> bool:
        if name in self.blacklisted_types or name in self.sdk_types: return False
        return not name.isupper() and not name.startswith(('OS', 'AL', 'gu'))

    def precision_sanitize(self, text: str) -> str:
        words = set(re.findall(r'\b([A-Z_][a-zA-Z0-9_]*)\b', text))
        for w in words:
            if self.is_custom_struct(w):
                self.discovered_structs.add(w)
                text = re.sub(rf'(?<!struct\s)\b{w}\b', f'struct {w}', text)
        return text

    def setup_workspace(self):
        print("[>] Finalizing Workspace for v74.1...")
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder): shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)
        for sub in ["src", "include"]:
            src, dst = os.path.join(self.decomp_path, sub), os.path.join(self.android_path, sub)
            if os.path.exists(src): shutil.copytree(src, dst, dirs_exist_ok=True)

    def harmonize_logic(self):
        print("[>] Implementing Weak-Alias Redirection...")
        # Enhanced regex to catch variadics and varied spacing
        func_pat = re.compile(r'^(([a-zA-Z_][\w\* ]*?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE)

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = hashlib.md5(os.path.relpath(path, self.src_target).encode()).hexdigest()[:8]
                
                with open(path, 'r', errors='ignore') as file:
                    content = file.read()

                def func_repl(m):
                    full_sig, ret_type, name, params = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
                    
                    # Hard-skip logic for internal and SDK symbols
                    if any(x in full_sig for x in ["static", "inline", "extern"]) or \
                       "..." in params or name.startswith(('os', 'al', 'gu', 'gS', 'gD')):
                        return m.group(0)

                    clean_ret = self.precision_sanitize(ret_type)
                    clean_params = self.precision_sanitize(params) or "void"
                    label = f"BKA_G_{fid}_{name}"
                    
                    self.global_symbols[name] = SymbolMapping(name, clean_ret, fid, clean_params, label)
                    
                    # Use a Weak Alias approach to allow function pointers to work naturally
                    return (f"\n#ifndef {name}\n"
                            f"{clean_ret} {name}({clean_params}) __attribute__((alias(\"{label}\")));\n"
                            f"{clean_ret} {label}({clean_params}) {{\n"
                            f"#else\n{m.group(0)}\n#endif")

                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n' + patched)

    def generate_header(self):
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n#include <ultra64.h>\n\n")
            for t in sorted(self.discovered_structs):
                f.write(f"struct {t};\n")
            
            f.write("\n// Aliased Global Symbols\n")
            for name, m in self.global_symbols.items():
                f.write(f"#ifndef {name}\nextern {m.type_info} {name}({m.params});\n#endif\n")
            f.write("\n#endif\n")

    def run(self):
        self.setup_workspace()
        self.harmonize_logic()
        self.generate_header()
        print("✓ Stabilization v74.1 Complete")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV74_1("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
