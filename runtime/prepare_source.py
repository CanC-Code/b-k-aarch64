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

class SourceHarmonizerV59:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        
        # Guard State
        self.reserved = {'bool', 'true', 'false', 'void', 'int', 'char', 'long', 'float', 'double', 'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64'}
        self.forbidden_symbols: Set[str] = set() # Macros, Enums, and existing Types
        self.discovered_types: Set[str] = set()
        self.func_signatures: Dict[str, FunctionSignature] = {}

    def get_file_id(self, filepath: str) -> str:
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:12]

    def setup_workspace(self):
        """Pass 0: Mirror environment setup."""
        print("[>] Pass 0: Syncing Workspace...")
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

    def deep_semantic_scan(self):
        """Pass 0.5: Neutralizes Enumerators and Macros to prevent 'different kind of symbol' errors."""
        print("[>] Pass 0.5: Building Neural Symbol Registry...")
        # Regex to catch: 
        # 1. #define MACRO
        # 2. enum { CONSTANT }
        # 3. typedef ExistingType
        patterns = [
            re.compile(r'#define\s+([A-Za-z_]\w+)'),
            re.compile(r'(\w+)\s*=\s*\d+'), # Enum values
            re.compile(r'typedef\s+.*?\s+(\w+);'),
            re.compile(r'\}\s*(\w+);')
        ]
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                        for p in patterns:
                            self.forbidden_symbols.update(p.findall(content))

    def process_logic(self):
        """Pass 1 & 2: Discover and link symbols with collision avoidance."""
        print("[>] Pass 1 & 2: Harmonizing Logic Flow...")
        func_pat = re.compile(r'^(?!.*inline)(?!.*extern)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        # We only look for CamelCase or types with _t, but exclude all-caps (usually macros/enums)
        type_pat = re.compile(r'\b([A-Z][a-z][a-zA-Z0-9_]+)\b')

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                with open(path, 'r', errors='ignore') as file: content = file.read()

                for t in type_pat.findall(content):
                    if t not in self.forbidden_symbols and t not in self.reserved:
                        self.discovered_types.add(t)

                def func_repl(m):
                    name = m.group(3).strip()
                    if name == 'main': return m.group(0)
                    self.func_signatures[f"{fid}_{name}"] = FunctionSignature(name, m.group(2).strip(), m.group(4).strip() or "void")
                    return f"#undef {name}\n#define GLOBAL_DEF_{fid}_{name}\n__attribute__((visibility(\"protected\"), used)) {m.group(1).replace(name, f'NL_{fid}_{name}', 1)} "

                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_header(self):
        """Pass 3: Final Opaque Linkage Header."""
        print("[>] Pass 3: Generating Neural-Link Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <stdbool.h>\n#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            for t in sorted(self.discovered_types):
                f.write(f"#if !defined({t}_DEFINED) && !defined({t})\n")
                f.write(f"  typedef struct {t} {t};\n  #define {t}_DEFINED\n#endif\n")
            
            for key, sig in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {sig.name}\n  #define {sig.name} NL_{key}\n  extern {sig.return_type} NL_{key}({sig.parameters});\n#endif\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v59.0 NEURAL-LINK")
        print("="*60)
        self.setup_workspace()
        self.deep_semantic_scan()
        self.process_logic()
        self.generate_header()
        
        print("\n" + "="*60)
        print("✓ NEURAL-LINK HARMONIZATION SUCCESSFUL")
        print("="*60)
        print(f"  [GUARD] Blocked Macros/Enums: {len(self.forbidden_symbols)}")
        print(f"  [TYPE] Validated Opaque Types: {len(self.discovered_types)}")
        print(f"  [FUNC] Globalized Symbols: {len(self.func_signatures)}")
        print("="*60 + "\n")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV59("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
