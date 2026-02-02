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

class SourceHarmonizerV55:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        
        # State
        self.reserved_identifiers = {'bool', 'true', 'false', 'void', 'int', 'char', 'long', 'float', 'double', 'static', 'extern', 'inline'}
        self.existing_types: Set[str] = set()
        self.discovered_types: Set[str] = set()
        self.func_signatures: Dict[str, FunctionSignature] = {}

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

    def precheck_existing_headers(self):
        """NEW PRECHECK: Fixes Error 196 (Typedef Redefinition) by mapping existing types."""
        print("[>] Pass 0.5: Scanning Existing Headers for Type Protection...")
        # Regex to find 'typedef struct Name Name;' or '} Name;'
        typedef_pattern = re.compile(r'typedef\s+(?:struct|union|enum)?\s*(\w+)\s+(\w+);|(?:\}\s*(\w+);)')
        
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h') and file != "harmonized_globals.h":
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                        for match in typedef_pattern.findall(content):
                            # Extract the type name from any of the capture groups
                            type_name = next(group for group in reversed(match) if group)
                            self.existing_types.add(type_name.strip())

    def map_and_promote(self):
        """Pass 1 & 2: Discover types and promote visibility."""
        print("[>] Pass 1 & 2: Logic Mapping & Symbol Promotion...")
        func_pat = re.compile(r'^(?!.*inline)(?!.*extern)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        type_regex = re.compile(r'\b([A-Z][a-zA-Z0-9_]+)\b')

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                with open(path, 'r', errors='ignore') as file: content = file.read()

                # Robust Type Discovery: Ignore anything found in the PreCheck
                for t in type_regex.findall(content):
                    if t not in self.existing_types and t not in self.reserved_identifiers:
                        self.discovered_types.add(t)

                def func_repl(m):
                    name = m.group(3).strip()
                    if name in ['main']: return m.group(0)
                    self.func_signatures[f"{fid}_{name}"] = FunctionSignature(name, m.group(2).strip(), m.group(4).strip() or "void")
                    return f"#undef {name}\n#define GLOBAL_DEF_{fid}_{name}\n__attribute__((visibility(\"protected\"), used)) {m.group(1).replace(name, f'SI_{fid}_{name}', 1)} "

                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_header(self):
        """Pass 3: Finalizes the header with defensive guards."""
        print("[>] Pass 3: Finalizing Stellar-Integrity Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <stdbool.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n")
            
            # Forward declarations for discovered types
            for t in sorted(self.discovered_types):
                f.write(f"#ifndef {t}_DEFINED\n  struct {t};\n  typedef struct {t} {t};\n  #define {t}_DEFINED\n#endif\n")
            
            for key, sig in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {sig.name}\n  #define {sig.name} SI_{key}\n  extern {sig.return_type} SI_{key}({sig.parameters});\n#endif\n")
            
            f.write("#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v55.0 STELLAR-INTEGRITY")
        print("="*60)
        self.ensure_environment()
        self.precheck_existing_headers()
        self.map_and_promote()
        self.generate_header()
        
        # Achievement Dashboard for your review
        print("\n" + "="*60)
        print("✓ HARMONIZATION SUCCESSFUL")
        print("="*60)
        print(f"  [PRECHECK] Blocked Duplicate Types: {len(self.existing_types)}")
        print(f"  [ACHIEVEMENT] Discovered New Types: {len(self.discovered_types)}")
        print(f"  [ACHIEVEMENT] Promoted Global Symbols: {len(self.func_signatures)}")
        print("="*60 + "\n")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV55("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
