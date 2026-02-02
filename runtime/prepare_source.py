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

class SourceHarmonizerV65:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        
        # Hard-coded safety for types that change shape across SDK versions
        self.immutables = {
            'bool', 'void', 'int', 'char', 'long', 'float', 'double', 
            'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64',
            'size_t', 'uintptr_t', 'intptr_t', 'Mtx', 'Gfx', 'Vtx', 'ADPCM_STATE',
            'ALMicroTime', 'ALID', 'OSMesg', 'OSThread', 'OSYieldResult'
        }
        self.conflict_registry: Set[str] = set() 
        self.discovered_types: Set[str] = set()
        self.func_signatures: List[FunctionSignature] = []

    def get_file_id(self, filepath: str) -> str:
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:8]

    def setup_workspace(self):
        """Pass 0: Environmental Restoration."""
        print("[>] Pass 0: Initializing Aether-Link Workspace...")
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

    def perform_introspection(self):
        """Pass 0.5: Registry of existing symbols to prevent 'kind-of-symbol' redefinitions."""
        print("[>] Pass 0.5: Performing Aether Introspection...")
        patterns = [
            re.compile(r'#define\s+([A-Za-z_]\w+)'),
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
                            self.conflict_registry.update(p.findall(content))

    def harmonize_logic(self):
        """Pass 1 & 2: Safe Linker Mapping with Variadic Support."""
        print("[>] Pass 1 & 2: Applying Aether-Link Mapping...")
        type_pat = re.compile(r'\b([A-Z][a-zA-Z0-9_]+)\b')
        func_pat = re.compile(r'^(static)\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                with open(path, 'r', errors='ignore') as file: content = file.read()

                for t in type_pat.findall(content):
                    if t not in self.conflict_registry and t not in self.immutables:
                        self.discovered_types.add(t)

                def func_repl(m):
                    name = m.group(4).strip()
                    if name in ('main', 'Entry'): return m.group(0)
                    
                    params = re.sub(r'\s+', ' ', m.group(5).strip()) or "void"
                    self.func_signatures.append(FunctionSignature(name, m.group(3).strip(), params, fid))
                    
                    # Direct Linker Assignment using Visibility Default for Android JNI
                    return f"__attribute__((visibility(\"default\"))) {m.group(2).replace(name, f'AL_{fid}_{name}', 1)} "

                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_header(self):
        """Pass 3: Generate the Final Global Aether Header."""
        print("[>] Pass 3: Finalizing Aether-Link Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <stdbool.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            f.write("/* Opaque Forward Declarations */\n")
            for t in sorted(self.discovered_types):
                # Triple-Guard to avoid any possible redefinition of existing structs
                f.write(f"#if !defined({t}_DEFINED) && !defined({t})\n")
                f.write(f"  typedef struct {t} {t};\n")
                f.write(f"  #define {t}_DEFINED\n")
                f.write(f"#endif\n")
            
            f.write("\n/* Symbol Redirection via Linker Labels */\n")
            for sig in self.func_signatures:
                # ASM labels are used to bypass the C macro processor entirely
                f.write(f"extern {sig.return_type} {sig.name}({sig.parameters}) __asm__(\"AL_{sig.file_id}_{sig.name}\");\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v65.0 AETHER-LINK")
        print("="*60)
        self.setup_workspace()
        self.perform_introspection()
        self.harmonize_logic()
        self.generate_header()
        print("\n" + "="*60)
        print("✓ AETHER-LINK HARMONIZATION COMPLETE")
        print(f"  Types Shielded:  {len(self.conflict_registry)}")
        print(f"  Mappings Active: {len(self.func_signatures)}")
        print("="*60 + "\n")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV65("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
