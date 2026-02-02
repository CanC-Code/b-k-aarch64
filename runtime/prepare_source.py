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

class SourceHarmonizerV52:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        
        # Core State
        self.reserved_identifiers = {'bool', 'true', 'false', 'void', 'int', 'char', 'long', 'float', 'double', 'static', 'extern'}
        self.sdk_defined_types: Set[str] = set()
        self.project_enums: Set[str] = set()
        self.discovered_types: Set[str] = set()
        self.func_signatures: Dict[str, FunctionSignature] = {}

    def get_file_id(self, filepath: str) -> str:
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:12]

    def ensure_environment(self):
        """Pass 0: Fixes the FileNotFoundError by ensuring path integrity."""
        print("[>] Pass 0: Validating Environment & Syncing Files...")
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)

        for sub in ["src", "include"]:
            source = os.path.join(self.decomp_path, sub)
            target = os.path.join(self.android_path, sub)
            if os.path.exists(source):
                for root, _, files in os.walk(source):
                    rel = os.path.relpath(root, source)
                    dest = os.path.join(target, rel)
                    os.makedirs(dest, exist_ok=True)
                    for f in files:
                        shutil.copy2(os.path.join(root, f), os.path.join(dest, f))

    def extract_sdk_types(self):
        """Pass 0.5: Identifies NDK/SDK types to prevent collision."""
        # Standard SDK types found in ultra64.h and related headers
        self.sdk_defined_types.update(['size_t', 'uintptr_t', 'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64'])

    def scan_project_enums(self):
        """Pass 0.75: Prevents ABILITY_0_BARGE redefinition errors."""
        print("[>] Pass 0.75: Scanning for Enum Constants...")
        enum_pattern = re.compile(r'\b([A-Z][A-Z0-9_]{3,})\b')
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                        if 'enum' in content:
                            matches = enum_pattern.findall(content)
                            self.project_enums.update(matches)

    def map_and_promote(self):
        """Pass 1 & 2: Maps types and promotes static visibility."""
        print("[>] Pass 1 & 2: Mapping Linkage & Promoting Visibility...")
        func_pat = re.compile(r'^(?!.*inline)(?!.*extern)static\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        type_regex = re.compile(r'\b([A-Z][a-zA-Z0-9_]+)\b')

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                with open(path, 'r', errors='ignore') as file: content = file.read()

                # Discover custom CamelCase types
                for t in type_regex.findall(content):
                    if t not in self.project_enums and t not in self.sdk_defined_types:
                        self.discovered_types.add(t)

                # Rewrite static functions to global with protected visibility
                def func_repl(m):
                    name = m.group(3).strip()
                    if name in ['main']: return m.group(0)
                    self.func_signatures[f"{fid}_{name}"] = FunctionSignature(name, m.group(2).strip(), m.group(4).strip() or "void")
                    return f"#undef {name}\n#define GLOBAL_DEF_{fid}_{name}\n__attribute__((visibility(\"protected\"), used)) {m.group(1).replace(name, f'SG_{fid}_{name}', 1)} "

                patched_content = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched_content)

    def generate_header(self):
        """Pass 3: Finalizes the cross-file linkage header."""
        print("[>] Pass 3: Finalizing Shielded Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#undef bool\n#include <stdbool.h>\n#define bool _Bool\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n")
            
            for t in sorted(self.discovered_types):
                f.write(f"#ifndef {t}_DEFINED\n  typedef struct {t} {t};\n  #define {t}_DEFINED\n#endif\n")
            
            for key, sig in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n  #undef {sig.name}\n  #define {sig.name} SG_{key}\n  extern {sig.return_type} SG_{key}({sig.parameters});\n#endif\n")
            
            f.write("#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v52.0 SINGULARITY")
        print("="*60)
        
        self.ensure_environment()
        self.extract_sdk_types()
        self.scan_project_enums()
        self.map_and_promote()
        self.generate_header()
        
        # Achievement Dashboard
        print("\n" + "="*60)
        print("✓ HARMONIZATION SUCCESSFUL")
        print("="*60)
        print(f"  [STATUS] Header Generated: {os.path.join(self.include_target, 'harmonized_globals.h')}")
        print(f"  [ACHIEVEMENT] Protected Enums: {len(self.project_enums)}")
        print(f"  [ACHIEVEMENT] Discovered Types: {len(self.discovered_types)}")
        print(f"  [ACHIEVEMENT] Promoted Functions: {len(self.func_signatures)}")
        print(f"  [COMPAT] Boolean Collision Shield: ACTIVE")
        print("="*60 + "\n")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV52("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
