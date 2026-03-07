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
    asm_label: str = ""

class SourceHarmonizerV73_6:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")

        # Types that MUST come from ultra64.h and should never be touched
        self.sdk_reserved = {
            'ALBank', 'ALSeq', 'ALInstrument', 'ALHeap', 'ALVoiceConfig',
            'OSMesg', 'OSThread', 'OSMesgQueue', 'Gfx', 'Mtx', 'Vtx', 'Acmd'
        }
        
        self.c_keywords = {'if', 'while', 'for', 'switch', 'return', 'sizeof', 'struct', 'typedef', 'union'}
        self.discovered_types: Set[str] = set()
        self.global_symbols: Dict[str, SymbolMapping] = {}

    def setup_workspace(self):
        print("[>] Initializing Workspace...")
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder): shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)
        for sub in ["src", "include"]:
            src, dst = os.path.join(self.decomp_path, sub), os.path.join(self.android_path, sub)
            if os.path.exists(src): shutil.copytree(src, dst, dirs_exist_ok=True)

    def is_sdk_type(self, name: str) -> bool:
        return name in self.sdk_reserved or name.startswith(('OS', 'AL', 'gbi', 'gu'))

    def harmonize_logic(self):
        print("[>] Applying Bridge Logic...")
        # Match function definitions: ret_type name(params) {
        func_pat = re.compile(r'^(([a-zA-Z_][\w\* ]*?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE)

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = hashlib.md5(os.path.relpath(path, self.src_target).encode()).hexdigest()[:6]
                
                with open(path, 'r', errors='ignore') as file:
                    content = file.read()

                def func_repl(m):
                    ret_type, name, params = m.group(2).strip(), m.group(3).strip(), m.group(4).strip() or "void"
                    
                    if name in self.c_keywords or self.is_sdk_type(name) or "static" in m.group(1):
                        return m.group(0)

                    # Extract potential custom types (Words starting with Uppercase)
                    for word in re.findall(r'\b([A-Z][a-zA-Z0-9_]+)\b', params + " " + ret_type):
                        if not self.is_sdk_type(word):
                            self.discovered_types.add(word)

                    label = f"BKA_G_{fid}_{name}"
                    self.global_symbols[name] = SymbolMapping(name, ret_type, fid, True, params, label)
                    
                    return f"\n#undef {name}\n{ret_type} {name} __asm__(\"{label}\")({params}) {{"

                # Injection: Use #include <ultra64.h> FIRST, then our bridge
                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_header(self):
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            f.write("// Bridge: Only forward declare types if they aren't SDK-reserved\n")
            for t in sorted(self.discovered_types):
                f.write(f"struct {t};\n")
            
            f.write("\n// Global Symbol Redirections\n")
            for name, m in self.global_symbols.items():
                f.write(f"extern {m.type_info} {name}({m.params}) __asm__(\"{m.asm_label}\");\n")
            f.write("\n#endif\n")

    def run(self):
        self.setup_workspace()
        self.harmonize_logic()
        self.generate_header()
        print("✓ Stabilization v73.6 Complete")

if __name__ == "__main__":
    # Point to your local paths
    harmonizer = SourceHarmonizerV73_6("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
