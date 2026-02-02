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

class SourceHarmonizerV62:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        
        # State Management
        self.system_types = {'bool', 'void', 'int', 'char', 'long', 'float', 'double', 'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64'}
        self.forbidden_symbols: Set[str] = set() 
        self.discovered_types: Set[str] = set()
        self.func_signatures: List[FunctionSignature] = []

    def get_file_id(self, filepath: str) -> str:
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:8]

    def setup_workspace(self):
        """Pass 0: Full sync with path preservation."""
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

    def build_registry(self):
        """Pass 0.5: Indexing existing symbols to prevent 'kind of symbol' errors."""
        print("[>] Pass 0.5: Indexing Existing Symbol Registry...")
        patterns = [
            re.compile(r'#define\s+([A-Za-z_]\w+)'),
            re.compile(r'(\w+)\s*=\s*-?\d+'), # Enums
            re.compile(r'typedef\s+.*?\s+(\w+);'),
            re.compile(r'(?:struct|union|enum)\s+(\w+)\s*\{')
        ]
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                        for p in patterns:
                            self.forbidden_symbols.update(p.findall(content))

    def harmonize(self):
        """Pass 1 & 2: Linker-level symbol redirection."""
        print("[>] Pass 1 & 2: Applying Linker Redirection...")
        # Static function detection
        func_pat = re.compile(r'^(static)\s+(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        type_pat = re.compile(r'\b([A-Z]\w+)\b')

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                with open(path, 'r', errors='ignore') as file: content = file.read()

                # Collect types used in this file
                for t in type_pat.findall(content):
                    if t not in self.forbidden_symbols and t not in self.system_types:
                        self.discovered_types.add(t)

                def func_repl(m):
                    name = m.group(4).strip()
                    if name == 'main': return m.group(0)
                    
                    sig = FunctionSignature(name, m.group(3).strip(), m.group(5).strip() or "void", fid)
                    self.func_signatures.append(sig)
                    
                    # Instead of #define, we use ASM Labels to rename the symbol at the object level
                    # This prevents macro collisions entirely.
                    return f"__attribute__((visibility(\"default\"))) {m.group(2).replace(name, f'SC_{fid}_{name}', 1)} "

                patched = re.sub(func_pat, func_repl, content)
                with open(path, 'w') as file:
                    file.write('#include "harmonized_globals.h"\n' + patched)

    def generate_header(self):
        """Pass 3: Generate the Core Linkage Header."""
        print("[>] Pass 3: Finalizing Singularity-Core Header...")
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n")
            f.write("#include <ultra64.h>\n#include <stdbool.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            f.write("/* Opaque Type Foundation */\n")
            for t in sorted(self.discovered_types):
                f.write(f"#if !defined({t}_DEFINED) && !defined({t})\n  typedef struct {t} {t};\n  #define {t}_DEFINED\n#endif\n")
            
            f.write("\n/* Linker-Level Function Mapping */\n")
            for sig in self.func_signatures:
                # We use the 'asm' label to map the original name to the unique hashed name
                # This is "Smart" because it doesn't use the preprocessor, avoiding redefinition errors.
                f.write(f"extern {sig.return_type} {sig.name}({sig.parameters}) __asm__(\"SC_{sig.file_id}_{sig.name}\");\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v62.0 SINGULARITY-CORE")
        print("="*60)
        self.setup_workspace()
        self.build_registry()
        self.harmonize()
        self.generate_header()
        print("\n" + "="*60)
        print("✓ SINGULARITY-CORE HARMONIZATION COMPLETE")
        print("="*60 + "\n")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV62("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
