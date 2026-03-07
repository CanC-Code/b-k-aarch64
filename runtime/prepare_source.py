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

class SourceHarmonizerV73_4:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")

        # Hard-blocked types that must NEVER be forward-declared (prevents Gfx/Mtx errors)
        self.immutables = {
            'bool', 'void', 'int', 'char', 'long', 'float', 'double', 'short',
            'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64',
            'Gfx', 'Mtx', 'Vtx', 'Vp', 'LookAt', 'Hilite', 'Light', 'Amb',
            'OSMesg', 'OSThread', 'OSMesgQueue', 'u_long', 'u_short', 'u_char'
        }
        
        self.c_keywords = {'if', 'while', 'for', 'switch', 'return', 'sizeof', 'struct', 'typedef', 'extern', 'static'}
        self.conflict_registry: Set[str] = set()
        self.discovered_types: Set[str] = set()
        self.all_function_names: Set[str] = set()
        self.global_symbols: Dict[str, SymbolMapping] = {}
        self.mappings: List[SymbolMapping] = []

    def remove_comments(self, text: str) -> str:
        return re.sub(r'/\*.*?\*/|//.*', '', text, flags=re.DOTALL)

    def setup_workspace(self):
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder): shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)
        # Re-copy files from decomp-files to Android workspace
        for sub in ["src", "include"]:
            src = os.path.join(self.decomp_path, sub)
            dst = os.path.join(self.android_path, sub)
            if os.path.exists(src): shutil.copytree(src, dst, dirs_exist_ok=True)

    def perform_introspection(self):
        """Builds a registry of every symbol already defined in N64 headers."""
        patterns = [
            re.compile(r'extern\s+[\w\* ]+\s+([A-Za-z_]\w*)\s*\('), # Functions
            re.compile(r'typedef\s+.*?\s+(\w+);'),                  # Typedefs
            re.compile(r'#define\s+([A-Za-z_]\w+)')                # Macros
        ]
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = self.remove_comments(f.read())
                        for p in patterns:
                            self.conflict_registry.update(p.findall(content))

    def harmonize_logic(self):
        # Improved regex to handle double pointers and complex return types
        func_pat = re.compile(r'^(static\s+)?(([a-zA-Z_][\w\* ]*?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE)
        data_pat = re.compile(r'^(static\s+)?([a-zA-Z_][\w\* ]*?)\s+([a-zA-Z_]\w*)\s*(?:=\s*([^;]+))?;', re.MULTILINE)

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = hashlib.md5(os.path.relpath(path, self.src_target).encode()).hexdigest()[:6]
                with open(path, 'r', errors='ignore') as file:
                    content = self.remove_comments(file.read())

                def func_repl(m):
                    is_static = m.group(1) is not None
                    ret_type, name, params = m.group(3).strip(), m.group(4).strip(), m.group(5).strip() or "void"
                    
                    if name in self.c_keywords or name in self.conflict_registry: return m.group(0)
                    self.all_function_names.add(name)

                    # Only treat Capitalized words as potential Struct types
                    for word in re.findall(r'\b([A-Z][a-zA-Z0-9_]+)\b', params + " " + ret_type):
                        if word not in self.immutables: self.discovered_types.add(word)

                    label = f"BK_{'S' if is_static else 'G'}_{fid}_{name}"
                    mapping = SymbolMapping(name, ret_type, fid, True, params, label)
                    if not is_static: self.global_symbols[name] = mapping
                    
                    return f"\n#undef {name}\n{m.group(1) or ''}{ret_type} {name} __asm__(\"{label}\")({params}) {{"

                patched = re.sub(func_pat, func_repl, content)
                # (Data replacement logic follows same pattern as func_repl)
                
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_header(self):
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        # Final safety filter: remove anything that turned out to be a function or SDK symbol
        final_types = self.discovered_types - self.all_function_names - self.conflict_registry

        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n#include <ultra64.h>\n")
            for t in sorted(final_types):
                f.write(f"typedef struct {t} {t};\n")
            for name, m in self.global_symbols.items():
                f.write(f"extern {m.type_info} {name}({m.params}) __asm__(\"{m.asm_label}\");\n")
            f.write("#endif\n")

    def run(self):
        self.setup_workspace()
        self.perform_introspection()
        self.harmonize_logic()
        self.generate_header()
        print("✓ Harmonization v73.4 Complete")

if __name__ == "__main__":
    SourceHarmonizerV73_4("Android/app/src/main/cpp", "decomp-files").run()
