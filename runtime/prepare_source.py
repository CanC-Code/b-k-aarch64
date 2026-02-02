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

class SourceHarmonizerV67:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        
        # Core primitives and SDK types that must never be modified
        self.immutables = {
            'bool', 'void', 'int', 'char', 'long', 'float', 'double', 
            'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64',
            'size_t', 'uintptr_t', 'intptr_t', 'Mtx', 'Gfx', 'Vtx', 'ADPCM_STATE',
            'ALMicroTime', 'ALID', 'OSMesg', 'OSThread', 'OSYieldResult', 'u_long',
            'OSPri', 'u_short', 'u_char'
        }
        self.conflict_registry: Set[str] = set() 
        self.discovered_types: Set[str] = set()
        self.func_signatures: List[FunctionSignature] = []

    def get_file_id(self, filepath: str) -> str:
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:8]

    def setup_workspace(self):
        """Pass 0: Full workspace synchronization."""
        print("[>] Pass 0: Initializing Omni-Bridge Workspace...")
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
        """Pass 0.5: Register all existing symbols to prevent redefinition errors."""
        print("[>] Pass 0.5: Building Omni-Symbol Registry...")
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
        """Pass 1 & 2: Linker Mapping with Macro-Redefinition Safety."""
        print("[>] Pass 1 & 2: Constructing Omni-Bridge Linkage...")
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
                    
                    full_sig_text = m.group(2)
                    params = re.sub(r'\s+', ' ', m.group(5).strip()) or "void"
                    self.func_signatures.append(FunctionSignature(name, m.group(3).strip(), params, fid))
                    
                    asm_name = f"OB_{fid}_{name}"
                    # Wrap the definition with #undef to prevent macro collision
                    # This ensures the __asm__ label is applied to the raw function name
                    return (f"\n#undef {name}\n"
                            f"__attribute__((used)) {full_sig_text.replace(name, f'{name} __asm__(\"{asm_name}\")', 1)} ")

                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_header(self):
        """Pass 3: Generate the Final Global Omni-Bridge Header."""
        print("[>] Pass 3: Finalizing Omni-Bridge Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <stdbool.h>\n#include <ultra64.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            f.write("/* Pass A: Collision-Proof Type Layer */\n")
            for t in sorted(self.discovered_types):
                f.write(f"#if !defined({t}_DEFINED) && !defined({t})\n")
                f.write(f"  typedef struct {t} {t};\n  #define {t}_DEFINED\n")
                f.write(f"#endif\n")
            
            f.write("\n/* Pass B: Omni-Bridge Symbol Mapping */\n")
            for sig in self.func_signatures:
                # Use undef in the header as well to ensure the extern mapping is clean
                f.write(f"#undef {sig.name}\n")
                f.write(f"extern {sig.return_type} {sig.name}({sig.parameters}) __asm__(\"OB_{sig.file_id}_{sig.name}\");\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v67.0 OMNI-BRIDGE")
        print("="*60)
        self.setup_workspace()
        self.perform_introspection()
        self.harmonize_logic()
        self.generate_header()
        print("\n" + "="*60)
        print("✓ OMNI-BRIDGE HARMONIZATION SUCCESSFUL")
        print(f"  Total Bridges: {len(self.func_signatures)}")
        print("="*60 + "\n")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV67("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
