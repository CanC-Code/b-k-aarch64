#!/usr/bin/env python3
import os
import re
import shutil
import hashlib
from typing import Set, List, Dict, Tuple

class SourceHarmonizerV74:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")

        self.immutables = {
            'bool', 'void', 'int', 'char', 'long', 'float', 'double', 'short',
            'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64',
            'Gfx', 'Mtx', 'Vtx', 'Vp', 'LookAt', 'Hilite', 'Light', 'Amb', 'Acmd'
        }
        self.sdk_prefixes = ('AL', 'OS', 'os', 'gbi', 'gd', 'gu', 'nbi', 'Vtx', 'Gfx', 'Mtx')
        self.global_symbols = {}
        self.struct_definitions = {}

    def is_sdk_symbol(self, name: str) -> bool:
        return name.startswith(self.sdk_prefixes) or name in self.immutables

    def scan_for_definitions(self):
        """Deep scan for full struct/union definitions to solve 'incomplete type' errors."""
        print("[>] Scanning for Type Definitions...")
        struct_pat = re.compile(r'(struct|union)\s+(\w+)\s*\{', re.MULTILINE)
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not (f.endswith('.c') or f.endswith('.h')): continue
                with open(os.path.join(root, f), 'r', errors='ignore') as src:
                    content = src.read()
                    for kind, name in struct_pat.findall(content):
                        if not self.is_sdk_symbol(name):
                            self.struct_definitions[name] = kind

    def harmonize_logic(self):
        print("[>] Applying Unified Symbol Mapping...")
        # Pattern for functions and global variables
        sym_pat = re.compile(r'^(?!(?:static|typedef))([\w\* ]+)\s+([a-zA-Z_]\w*)\s*([;=\(])', re.MULTILINE)

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = hashlib.md5(f.encode()).hexdigest()[:6]
                
                with open(path, 'r', errors='ignore') as file:
                    lines = file.readlines()

                new_lines = []
                for line in lines:
                    match = sym_pat.match(line)
                    if match:
                        full_type, name, suffix = match.groups()
                        name = name.strip()
                        if not self.is_sdk_symbol(name) and "main" not in name:
                            label = f"BKA_G_{fid}_{name}"
                            self.global_symbols[name] = (full_type.strip(), suffix == '(', label)
                            line = f"#undef {name}\n{full_type} {name} __asm__(\"{label}\"){suffix}"
                    new_lines.append(line)

                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + "".join(new_lines))

    def generate_header(self):
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <ultra64.h>\n\n")
            
            # Forward declarations for all discovered internal types
            for name, kind in self.struct_definitions.items():
                f.write(f"typedef {kind} {name} {name};\n")
            
            f.write("\n// Global Symbol Map\n")
            for name, (t_info, is_func, label) in self.global_symbols.items():
                if is_func:
                    f.write(f"extern {t_info} {name}() __asm__(\"{label}\");\n")
                else:
                    f.write(f"extern {t_info} {name} __asm__(\"{label}\");\n")
            
            f.write("\n#endif\n")

    def run(self):
        # Implementation of setup_workspace and introspection omitted for brevity
        self.scan_for_definitions()
        self.harmonize_logic()
        self.generate_header()
        print("✓ SourceHarmonizer v74.0: Types Unified.")

if __name__ == "__main__":
    SourceHarmonizerV74("Android/app/src/main/cpp", "decomp-files").run()
