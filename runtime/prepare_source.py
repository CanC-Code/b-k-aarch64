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

class SourceHarmonizerV54:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        
        # State Tracking
        self.reserved_identifiers = {'bool', 'true', 'false', 'void', 'int', 'char', 'long', 'float', 'double', 'static', 'extern'}
        self.predefined_types: Set[str] = set()
        self.discovered_types: Set[str] = set()
        self.func_signatures: Dict[str, FunctionSignature] = {}
        
        # DYNAMIC BLACKLIST: Based on log errors (Fixes Error 19 & 547)
        self.dynamic_blacklist = {'ADPCM_STATE', 'ADPCMFSIZE', 'ADPCMVSIZE', 'AI_BITRATE_REG'}

    def get_file_id(self, filepath: str) -> str:
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:12]

    def ensure_environment(self):
        """Pass 0: Establishes directory structure and syncs files."""
        print("[>] Pass 0: Validating Environment...")
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

    def precheck_type_integrity(self):
        """Pass 0.5: Maps existing header types to prevent redefinition."""
        print("[>] Pass 0.5: Mapping Existing Header Types...")
        # Matches various typedef styles to avoid collision
        typedef_pattern = re.compile(r'typedef\s+(?:struct|union|enum)?\s*([\w\s\*]+?)\s*(\w+);|(?:\}\s*(\w+);)')
        
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                        for match in typedef_pattern.findall(content):
                            type_name = next(group for group in reversed(match) if group)
                            self.predefined_types.add(type_name.strip())

    def map_and_promote(self):
        """Pass 1 & 2: Dynamic symbol discovery and visibility promotion."""
        print("[>] Pass 1 & 2: Dynamic Symbol Promotion...")
        func_pat = re.compile(r'^(?!.*inline)(?!.*extern)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        type_regex = re.compile(r'\b([A-Z][a-zA-Z0-9_]+)\b')

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                with open(path, 'r', errors='ignore') as file: content = file.read()

                # Robust Type Discovery (Checks blacklist and pre-existing types)
                for t in type_regex.findall(content):
                    if (t not in self.predefined_types and 
                        t not in self.reserved_identifiers and 
                        t not in self.dynamic_blacklist):
                        self.discovered_types.add(t)

                def func_repl(m):
                    name = m.group(3).strip()
                    if name in ['main']: return m.group(0)
                    self.func_signatures[f"{fid}_{name}"] = FunctionSignature(name, m.group(2).strip(), m.group(4).strip() or "void")
                    return f"#undef {name}\n#define GLOBAL_DEF_{fid}_{name}\n__attribute__((visibility(\"protected\"), used)) {m.group(1).replace(name, f'SX_{fid}_{name}', 1)} "

                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_header(self):
        """Pass 3: Generates the finalized header with 'Named Opaque Pointer' pattern."""
        print("[>] Pass 3: Finalizing Singularity-X Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#undef bool\n#include <stdbool.h>\n#define bool _Bool\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n")
            
            # Named Struct Pattern (Fixes Error 13, 14: anonymous struct definition error)
            for t in sorted(self.discovered_types):
                f.write(f"#ifndef {t}_DEFINED\n  struct {t}_s;\n  typedef struct {t}_s {t};\n  #define {t}_DEFINED\n#endif\n")
            
            for key, sig in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {sig.name}\n  #define {sig.name} SX_{key}\n  extern {sig.return_type} SX_{key}({sig.parameters});\n#endif\n")
            
            f.write("#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v54.0 SINGULARITY-X")
        print("="*60)
        self.ensure_environment()
        self.precheck_type_integrity()
        self.map_and_promote()
        self.generate_header()
        
        # Dynamic Achievement Dashboard
        print("\n" + "="*60)
        print("✓ HARMONIZATION SUCCESSFUL")
        print("="*60)
        print(f"  [PRECHECK] Blocked Built-in Types: {len(self.predefined_types)}")
        print(f"  [DYNAMIC] Blacklisted Collisions: {len(self.dynamic_blacklist)}")
        print(f"  [ACHIEVEMENT] New Opaque Typedefs: {len(self.discovered_types)}")
        print(f"  [ACHIEVEMENT] Promoted Local Symbols: {len(self.func_signatures)}")
        print("="*60 + "\n")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV54("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
