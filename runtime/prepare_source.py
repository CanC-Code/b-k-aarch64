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

class SourceHarmonizerV56:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        
        # Comprehensive State
        self.system_reserved = {'bool', 'true', 'false', 'void', 'int', 'char', 'long', 'float', 'double', 'static', 'extern', 'inline', 'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64'}
        self.existing_registry: Set[str] = set()
        self.discovered_types: Set[str] = set()
        self.func_signatures: Dict[str, FunctionSignature] = {}

    def get_file_id(self, filepath: str) -> str:
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:12]

    def ensure_environment(self):
        """Pass 0: Infrastructure Setup"""
        print("[>] Pass 0: Initializing Aegis Environment...")
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder): shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)

        for sub in ["src", "include"]:
            source = os.path.join(self.decomp_path, sub)
            target = os.path.join(self.android_path, sub)
            if os.path.exists(source):
                for root, _, files in os.walk(source):
                    rel = os.path.relpath(root, source)
                    dest = os.path.join(target, rel)
                    os.makedirs(dest, exist_ok=True)
                    for f in files: shutil.copy2(os.path.join(root, f), os.path.join(dest, f))

    def dynamic_type_check(self):
        """Pass 0.5: Self-Correcting Registry. Scans for existing definitions to prevent Error 196."""
        print("[>] Pass 0.5: Building Aegis Type Registry...")
        # Matches: typedef [any] Name;  OR struct Name { ... }; OR enum Name { ... };
        patterns = [
            re.compile(r'typedef\s+.*?\s+(\w+);', re.DOTALL),
            re.compile(r'\}\s*(\w+);'),
            re.compile(r'(?:struct|union|enum)\s+(\w+)\s*\{')
        ]
        
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                        for p in patterns:
                            for match in p.findall(content):
                                self.existing_registry.add(match.strip())

    def map_and_promote(self):
        """Pass 1 & 2: Symbol Extraction and Namespace Protection."""
        print("[>] Pass 1 & 2: Global Linkage Entanglement...")
        func_pat = re.compile(r'^(?!.*inline)(?!.*extern)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        # Identifies CamelCase types likely needing forward declarations
        type_candidate_pat = re.compile(r'\b([A-Z][a-zA-Z0-9_]+)\b')

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                with open(path, 'r', errors='ignore') as file: content = file.read()

                # Dynamic Filtering: Only discover types that aren't already in the registry
                for t in type_candidate_pat.findall(content):
                    if t not in self.existing_registry and t not in self.system_reserved:
                        self.discovered_types.add(t)

                def func_repl(m):
                    name = m.group(3).strip()
                    if name in ['main']: return m.group(0)
                    self.func_signatures[f"{fid}_{name}"] = FunctionSignature(name, m.group(2).strip(), m.group(4).strip() or "void")
                    return f"#undef {name}\n#define GLOBAL_DEF_{fid}_{name}\n__attribute__((visibility(\"protected\"), used)) {m.group(1).replace(name, f'AG_{fid}_{name}', 1)} "

                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_header(self):
        """Pass 3: Triple-Guarded Aegis Header."""
        print("[>] Pass 3: Finalizing Aegis-Dynamic Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <stdbool.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            # Triple-Guard Pattern: Prevents "redefinition as different kind of symbol"
            for t in sorted(self.discovered_types):
                f.write(f"#if !defined({t}_DEFINED) && !defined({t})\n")
                f.write(f"  struct {t};\n  typedef struct {t} {t};\n")
                f.write(f"  #define {t}_DEFINED\n")
                f.write(f"#endif\n")
            
            for key, sig in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {sig.name}\n  #define {sig.name} AG_{key}\n  extern {sig.return_type} AG_{key}({sig.parameters});\n#endif\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v56.0 AEGIS-DYNAMIC")
        print("="*60)
        self.ensure_environment()
        self.dynamic_type_check()
        self.map_and_promote()
        self.generate_header()
        
        print("\n" + "="*60)
        print("✓ AEGIS HARMONIZATION COMPLETE")
        print("="*60)
        print(f"  [REGISTRY] Blocked Existing Types: {len(self.existing_registry)}")
        print(f"  [AEGIS] Dynamically Shielded Types: {len(self.discovered_types)}")
        print(f"  [LINKAGE] Promoted Local Symbols: {len(self.func_signatures)}")
        print("="*60 + "\n")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV56("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
