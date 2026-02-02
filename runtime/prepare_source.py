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

class SourceHarmonizerV51:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        
        self.reserved_identifiers = {'bool', 'true', 'false', 'void', 'int', 'char', 'long', 'float', 'double', 'static', 'extern'}
        self.sdk_defined_types: Set[str] = set()
        self.project_enums: Set[str] = set()
        self.discovered_types: Set[str] = set()
        self.func_signatures: Dict[str, FunctionSignature] = {}

    def get_file_id(self, filepath: str) -> str:
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:12]

    def sync_files(self):
        """Pass 0: Ensure directories exist and copy fresh files."""
        print("[>] Pass 0: Synchronizing Directories...")
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

    def scan_project_enums(self):
        """Pass 0.75: Critical fix for enum constant vs struct conflicts."""
        print("[>] Pass 0.75: Protecting Project Enums...")
        enum_pattern = re.compile(r'\b([A-Z][A-Z0-9_]{3,})\b')
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                        if 'enum' in content:
                            self.project_enums.update(enum_pattern.findall(content))

    def map_and_promote(self):
        """Pass 1 & 2: Discover types and rename static symbols for global visibility."""
        print("[>] Pass 1 & 2: Symbol Extraction & Promotion...")
        # Matches static functions that are not inline
        func_pat = re.compile(r'^(?!.*inline)(?!.*extern)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        type_regex = re.compile(r'\b([A-Z][a-zA-Z0-9_]+)\b')

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                with open(path, 'r', errors='ignore') as file: content = file.read()

                # Extract Types
                for t in type_regex.findall(content):
                    if t not in self.project_enums and t not in self.reserved_identifiers:
                        self.discovered_types.add(t)

                # Promote Static Functions to Global (Protected Visibility)
                def func_repl(m):
                    name = m.group(3).strip()
                    if name in ['main']: return m.group(0)
                    self.func_signatures[f"{fid}_{name}"] = FunctionSignature(name, m.group(2).strip(), m.group(4).strip() or "void")
                    return f"#undef {name}\n#define GLOBAL_DEF_{fid}_{name}\n__attribute__((visibility(\"protected\"), used)) {m.group(1).replace(name, f'OM_{fid}_{name}', 1)} "

                new_content = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + new_content)

    def generate_header(self):
        """Pass 3: Finalize the shielded global header."""
        print("[>] Pass 3: Generating Shielded Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#undef bool\n#include <stdbool.h>\n#define bool _Bool\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n")
            
            for t in sorted(self.discovered_types):
                f.write(f"#ifndef {t}_DEF\n  typedef struct {t} {t};\n  #define {t}_DEF\n#endif\n")
            
            for key, sig in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {sig.name}\n  #define {sig.name} OM_{key}\n  extern {sig.return_type} OM_{key}({sig.parameters});\n#endif\n")
            
            f.write("#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        print("Banjo-Kazooie Source Harmonizer v51.0 OMEGA")
        self.sync_files()
        self.scan_project_enums()
        self.map_and_promote()
        self.generate_header()
        print("✓ Harmonization Complete: v51.0 Applied")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV51("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
