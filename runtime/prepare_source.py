#!/usr/bin/env python3
import os
import re
import shutil
import hashlib
from typing import Dict, Set, List
from dataclasses import dataclass

@dataclass
class FunctionSignature:
    name: str
    return_type: str
    parameters: str

class SourceHarmonizerV61:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        
        # Enhanced Protection State
        self.reserved = {'bool', 'true', 'false', 'void', 'int', 'char', 'long', 'float', 'double', 'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64'}
        self.forbidden_symbols: Set[str] = set() 
        self.discovered_types: Set[str] = set()
        self.func_signatures: Dict[str, FunctionSignature] = {}

    def get_file_id(self, filepath: str) -> str:
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:12]

    def setup_workspace(self):
        """Pass 0: Environmental Synchronization."""
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

    def build_symbol_registry(self):
        """Pass 0.5: Deep Recursive Header Scan for Type & Constant Protection."""
        patterns = [
            re.compile(r'#define\s+([A-Za-z_]\w+)'),
            re.compile(r'(\w+)\s*=\s*-?\d+'), # Enum constants
            re.compile(r'typedef\s+.*?\s+(\w+);'),
            re.compile(r'\}\s*(\w+);'),
            re.compile(r'(?:struct|union|enum)\s+(\w+)')
        ]
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                        for p in patterns:
                            self.forbidden_symbols.update(p.findall(content))

    def harmonize_logic(self):
        """Pass 1 & 2: Dynamic Type Discovery and QL-Namespace Application."""
        func_pat = re.compile(r'^(?!.*inline)(?!.*extern)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        # Enhanced type detection for pointers and return types
        type_detection_pat = re.compile(r'\b([A-Z]\w+)\b(?!\s*\()')

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                with open(path, 'r', errors='ignore') as file: content = file.read()

                # Dynamically discover all unique types used in function context
                for t in type_detection_pat.findall(content):
                    if t not in self.forbidden_symbols and t not in self.reserved:
                        self.discovered_types.add(t)

                def func_repl(m):
                    name = m.group(3).strip()
                    if name == 'main': return m.group(0)
                    self.func_signatures[f"{fid}_{name}"] = FunctionSignature(name, m.group(2).strip(), m.group(4).strip() or "void")
                    return f"#undef {name}\n#define GLOBAL_DEF_{fid}_{name}\n__attribute__((visibility(\"protected\"), used)) {m.group(1).replace(name, f'QL_{fid}_{name}', 1)} "

                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_quantum_header(self):
        """Pass 3: Final Global Linkage Header with Smart Guards."""
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <stdbool.h>\n#include <ultra64.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            f.write("/* --- STAGE 1: DYNAMIC OPAQUE TYPES --- */\n")
            # Sort types to maintain build consistency
            for t in sorted(self.discovered_types):
                f.write(f"#if !defined({t}_DEFINED) && !defined({t})\n")
                f.write(f"  typedef struct {t} {t};\n  #define {t}_DEFINED\n#endif\n")
            
            f.write("\n/* --- STAGE 2: GLOBALIZED SYMBOL LINKAGE --- */\n")
            for key, sig in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {sig.name}\n  #define {sig.name} QL_{key}\n  extern {sig.return_type} QL_{key}({sig.parameters});\n#endif\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v61.0 QUANTUM-LINK")
        print("="*60)
        self.setup_workspace()
        self.build_symbol_registry()
        self.harmonize_logic()
        self.generate_quantum_header()
        
        print("\n" + "="*60)
        print("✓ QUANTUM-LINK HARMONIZATION SUCCESSFUL")
        print("="*60)
        print(f"  Blocked Symbols (Conflicts): {len(self.forbidden_symbols)}")
        print(f"  Discovered Dynamic Types:    {len(self.discovered_types)}")
        print(f"  Globalized Functions:        {len(self.func_signatures)}")
        print("="*60 + "\n")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV61("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
