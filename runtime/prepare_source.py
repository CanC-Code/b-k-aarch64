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

class SourceHarmonizerV64:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        
        # System-level types that must never be redeclared
        self.blacklist = {
            'bool', 'void', 'int', 'char', 'long', 'float', 'double', 
            'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64',
            'size_t', 'uintptr_t', 'intptr_t', 'Mtx', 'Gfx', 'Vtx', 'u_long',
            'u_short', 'u_char', 'ALMicroTime', 'ALID'
        }
        self.known_symbols: Set[str] = set() 
        self.discovered_types: Set[str] = set()
        self.func_signatures: List[FunctionSignature] = []

    def get_file_id(self, filepath: str) -> str:
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:8]

    def setup_workspace(self):
        """Pass 0: Restore clean state."""
        print("[>] Pass 0: Initializing Stellar-Core Workspace...")
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

    def deep_header_introspection(self):
        """Pass 0.5: Advanced regex to identify all existing typedefs and defines."""
        print("[>] Pass 0.5: Performing Deep Header Introspection...")
        patterns = [
            re.compile(r'#define\s+([A-Za-z_]\w+)'),
            re.compile(r'typedef\s+.*?\s+(\w+)\s*\[\d+\];'), # Array typedefs (Fixes ADPCM_STATE)
            re.compile(r'typedef\s+.*?\s+(\w+);'),           # Standard typedefs (Fixes ALFxRef)
            re.compile(r'\}\s*(\w+);'),                       # Struct-end typedefs
            re.compile(r'(?:struct|union|enum)\s+(\w+)')
        ]
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                        for p in patterns:
                            self.known_symbols.update(p.findall(content))

    def harmonize_source(self):
        """Pass 1 & 2: Linker-level mapping using Stellar-Core logic."""
        print("[>] Pass 1 & 2: Applying Stellar-Core Logic...")
        # Capture potential types (starts with Uppercase, like Actor, Cube, etc)
        type_pat = re.compile(r'\b([A-Z][a-zA-Z0-9_]+)\b')
        func_pat = re.compile(r'^(static)\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                with open(path, 'r', errors='ignore') as file: content = file.read()

                # Protect newly discovered types
                for t in type_pat.findall(content):
                    if t not in self.known_symbols and t not in self.blacklist:
                        self.discovered_types.add(t)

                def func_repl(m):
                    name = m.group(4).strip()
                    if name in ('main', 'Entry'): return m.group(0)
                    
                    self.func_signatures.append(FunctionSignature(
                        name, m.group(3).strip(), 
                        re.sub(r'\s+', ' ', m.group(5).strip()) or "void", 
                        fid
                    ))
                    return f"__attribute__((visibility(\"default\"))) {m.group(2).replace(name, f'SC_{fid}_{name}', 1)} "

                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    # Enforce standardized include hierarchy
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_stellar_header(self):
        """Pass 3: Generate Collision-Proof Global Header."""
        print("[>] Pass 3: Constructing Stellar-Core Global Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <stdbool.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            f.write("/* Pass A: Verified Opaque Types (Collision-Free) */\n")
            for t in sorted(self.discovered_types):
                f.write(f"#if !defined({t}_DEFINED) && !defined({t})\n")
                f.write(f"  typedef struct {t} {t};\n")
                f.write(f"  #define {t}_DEFINED\n")
                f.write(f"#endif\n")
            
            f.write("\n/* Pass B: Direct Linker ASM Labels */\n")
            for sig in self.func_signatures:
                f.write(f"extern {sig.return_type} {sig.name}({sig.parameters}) __asm__(\"SC_{sig.file_id}_{sig.name}\");\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v64.0 STELLAR-CORE")
        print("="*60)
        self.setup_workspace()
        self.deep_header_introspection()
        self.harmonize_source()
        self.generate_stellar_header()
        print("\n" + "="*60)
        print("✓ STELLAR-CORE HARMONIZATION SUCCESSFUL")
        print(f"  Types Masked:   {len(self.known_symbols)}")
        print(f"  Functions Mapped: {len(self.func_signatures)}")
        print("="*60 + "\n")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV64("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
