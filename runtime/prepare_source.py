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

class SourceHarmonizerV73_9:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")

        self.blacklisted_types = {
            'NULL', 'TRUE', 'FALSE', 'VI_NTSC_CLOCK', 'static', 'inline', 'extern', 'void'
        }
        
        # Hard-Exclude: These must NEVER be prefixed with 'struct'
        self.sdk_types = {
            'ALBank', 'ALSeq', 'ALInstrument', 'ALHeap', 'ALVoiceConfig',
            'OSMesg', 'OSThread', 'OSMesgQueue', 'Gfx', 'Mtx', 'Vtx', 'Acmd',
            'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64',
            'sint', 'uint', 'size_t', 'uintptr_t', 'intptr_t', 'Vp', 'Lightsn', 'Light'
        }
        
        self.discovered_structs: Set[str] = set()
        self.global_symbols: Dict[str, SymbolMapping] = {}

    def is_custom_struct(self, name: str) -> bool:
        if name in self.blacklisted_types or name in self.sdk_types: return False
        if name.startswith(('OS', 'AL', 'gbi', 'gu', 'BKA_')): return False
        return not name.isupper()

    def setup_workspace(self):
        print("[>] Preparing Final Workspace...")
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder): shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)
        for sub in ["src", "include"]:
            src, dst = os.path.join(self.decomp_path, sub), os.path.join(self.android_path, sub)
            if os.path.exists(src): shutil.copytree(src, dst, dirs_exist_ok=True)

    def precision_sanitize(self, text: str) -> str:
        words = set(re.findall(r'\b([A-Z_][a-zA-Z0-9_]*)\b', text))
        for w in words:
            if self.is_custom_struct(w):
                self.discovered_structs.add(w)
                text = re.sub(rf'(?<!struct\s)\b{w}\b', f'struct {w}', text)
        return text

    def harmonize_logic(self):
        print("[>] Executing Symbol Redirection v73.9...")
        # Capture signature, ret type, name, and params
        func_pat = re.compile(r'^(([a-zA-Z_][\w\* ]*?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE)

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                # Use 8-char hash to prevent symbol collisions
                fid = hashlib.md5(os.path.relpath(path, self.src_target).encode()).hexdigest()[:8]
                
                with open(path, 'r', errors='ignore') as file:
                    content = file.read()

                def func_repl(m):
                    full_sig, ret_type, name, params = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
                    
                    # IGNORE: static, inline, extern, variadics, and SDK prefixes
                    if any(x in full_sig for x in ["static", "inline", "extern", "..."]) or \
                       name.startswith(('os', 'al', 'gu', 'main')):
                        return m.group(0)

                    clean_ret = self.precision_sanitize(ret_type)
                    clean_params = self.precision_sanitize(params) or "void"

                    label = f"BKA_G_{fid}_{name}"
                    self.global_symbols[name] = SymbolMapping(name, clean_ret, fid, True, clean_params, label)
                    
                    return f"\n{clean_ret} {name} __asm__(\"{label}\")({clean_params}) {{"

                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n' + patched)

    def generate_header(self):
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <ultra64.h>\n\n")
            
            f.write("// Forward Declarations for Custom Types\n")
            for t in sorted(self.discovered_structs):
                f.write(f"struct {t};\n")
            
            f.write("\n// Linker-Level Function Redirection\n")
            for name, m in self.global_symbols.items():
                f.write(f"extern {m.type_info} {name}({m.params}) __asm__(\"{m.asm_label}\");\n")
                
            f.write("\n#endif\n")

    def run(self):
        self.setup_workspace()
        self.harmonize_logic()
        self.generate_header()
        print("✓ Stabilization v73.9 Complete")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV73_9("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
