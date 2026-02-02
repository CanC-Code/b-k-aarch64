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
    file_id: str

class SourceHarmonizerV63:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        
        # Comprehensive System Blacklist
        self.blacklist = {
            'bool', 'void', 'int', 'char', 'long', 'float', 'double', 
            'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64',
            'size_t', 'uintptr_t', 'intptr_t', 'Mtx', 'Gfx', 'Vtx', 'u_long'
        }
        self.known_symbols: Set[str] = set() 
        self.discovered_types: Set[str] = set()
        self.func_signatures: List[FunctionSignature] = []

    def get_file_id(self, filepath: str) -> str:
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:8]

    def setup_workspace(self):
        """Pass 0: Mirror environment with absolute path safety."""
        print("[>] Pass 0: Initializing Event-Horizon Workspace...")
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

    def scan_for_conflicts(self):
        """Pass 0.5: Registry of every macro, enum, and typedef in the project."""
        print("[>] Pass 0.5: Mapping Global Conflict Registry...")
        patterns = [
            re.compile(r'#define\s+([A-Za-z_]\w+)'),
            re.compile(r'(\w+)\s*=\s*-?\d+'), 
            re.compile(r'typedef\s+.*?\s+(\w+);'),
            re.compile(r'(?:struct|union|enum)\s+(\w+)')
        ]
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                        for p in patterns:
                            self.known_symbols.update(p.findall(content))

    def harmonize_c_files(self):
        """Pass 1 & 2: Static Symbol Redirection using ASM Labels."""
        print("[>] Pass 1 & 2: Harmonizing C Logic and Linkage...")
        func_pat = re.compile(r'^(static)\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        type_pat = re.compile(r'\b([A-Z][a-zA-Z0-9_]+)\b')

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                with open(path, 'r', errors='ignore') as file: content = file.read()

                # Collect custom types to forward declare
                for t in type_pat.findall(content):
                    if t not in self.known_symbols and t not in self.blacklist:
                        self.discovered_types.add(t)

                def func_repl(m):
                    name = m.group(4).strip()
                    if name in ('main', 'Entry'): return m.group(0)
                    
                    # Store signature for global header
                    self.func_signatures.append(FunctionSignature(
                        name, m.group(3).strip(), 
                        re.sub(r'\s+', ' ', m.group(5).strip()) or "void", 
                        fid
                    ))
                    
                    # Direct Linker Assignment: Original Name -> Hashed Name
                    return f"__attribute__((visibility(\"default\"))) {m.group(2).replace(name, f'EH_{fid}_{name}', 1)} "

                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    # Explicit order to solve type shadowing
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_final_header(self):
        """Pass 3: Final Global Header with Atomic Protection."""
        print("[>] Pass 3: Constructing Atomic Linkage Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <stdbool.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            f.write("/* Pass A: Opaque Type Foundation */\n")
            for t in sorted(self.discovered_types):
                f.write(f"#if !defined({t}_DEFINED) && !defined({t})\n")
                f.write(f"  typedef struct {t} {t};\n")
                f.write(f"  #define {t}_DEFINED\n")
                f.write(f"#endif\n")
            
            f.write("\n/* Pass B: ASM Linker Mapping */\n")
            for sig in self.func_signatures:
                # ASM labels bypass the C preprocessor, making them collision-proof
                f.write(f"extern {sig.return_type} {sig.name}({sig.parameters}) __asm__(\"EH_{sig.file_id}_{sig.name}\");\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v63.0 EVENT-HORIZON")
        print("="*60)
        self.setup_workspace()
        self.scan_for_conflicts()
        self.harmonize_c_files()
        self.generate_final_header()
        print("\n" + "="*60)
        print("✓ EVENT-HORIZON HARMONIZATION SUCCESSFUL")
        print(f"  Linker Mappings Generated: {len(self.func_signatures)}")
        print(f"  Opaque Types Protected:    {len(self.discovered_types)}")
        print("="*60 + "\n")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV63("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
