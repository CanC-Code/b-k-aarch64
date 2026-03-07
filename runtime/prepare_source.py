#!/usr/bin/env python3
import os
import re
import shutil
import hashlib
from typing import Set, Dict
from dataclasses import dataclass

@dataclass
class SymbolMapping:
    name: str
    type_info: str
    file_id: str
    params: str = ""
    asm_label: str = ""

class SourceHarmonizerV74_2:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")

        # Refined blacklist to avoid breaking core logic
        self.blacklisted_types = {'NULL', 'TRUE', 'FALSE', 'static', 'inline', 'extern', 'void', 's32', 'u32', 'f32'}
        self.discovered_structs: Set[str] = set()
        self.global_symbols: Dict[str, SymbolMapping] = {}

    def is_custom_struct(self, name: str) -> bool:
        if name in self.blacklisted_types: return False
        # Only treat it as a custom struct if it's not all uppercase (macros) 
        # and doesn't look like a standard primitive
        return not name.isupper() and len(name) > 2

    def precision_sanitize(self, text: str) -> str:
        # Standardize 'struct Name' usage without overriding existing definitions
        words = set(re.findall(r'\b([A-Z_][a-zA-Z0-9_]*)\b', text))
        for w in words:
            if self.is_custom_struct(w):
                self.discovered_structs.add(w)
                text = re.sub(rf'(?<!struct\s)\b{w}\b', f'struct {w}', text)
        return text

    def setup_workspace(self):
        print("[>] Preparing v74.2 Workspace...")
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder): shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)
        for sub in ["src", "include"]:
            src, dst = os.path.join(self.decomp_path, sub), os.path.join(self.android_path, sub)
            if os.path.exists(src): shutil.copytree(src, dst, dirs_exist_ok=True)

    def harmonize_logic(self):
        print("[>] Applying Definition-Safe Redirection...")
        # Matches function definitions at start of line
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
                    
                    # Skip if it's a known internal/static function or a variadic
                    if any(x in full_sig for x in ["static", "inline"]) or "..." in params:
                        return m.group(0)

                    clean_ret = self.precision_sanitize(ret_type)
                    clean_params = self.precision_sanitize(params) or "void"
                    label = f"BKA_G_{fid}_{name}"
                    
                    self.global_symbols[name] = SymbolMapping(name, clean_ret, fid, clean_params, label)
                    
                    # Use ASM label directly on the definition to maintain type integrity 
                    # within the translation unit.
                    return f"{clean_ret} {name} __asm__(\"{label}\")({clean_params}) {{"

                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    # We no longer force ultra64.h at the top to avoid redefinition loops;
                    # we rely on the file's original includes.
                    file.write(patched)

    def generate_header(self):
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            
            # Forward declarations for discovered types
            for t in sorted(self.discovered_structs):
                f.write(f"struct {t};\n")
            
            f.write("\n// Global Redirections\n")
            for name, m in self.global_symbols.items():
                f.write(f"extern {m.type_info} {name}({m.params}) __asm__(\"{m.asm_label}\");\n")
            f.write("\n#endif\n")

    def run(self):
        self.setup_workspace()
        self.harmonize_logic()
        self.generate_header()
        print("✓ Stabilization v74.2 Complete")

if __name__ == "__main__":
    # Ensure paths match your environment
    harmonizer = SourceHarmonizerV74_2("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
