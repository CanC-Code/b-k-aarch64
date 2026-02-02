#!/usr/bin/env python3
import os
import re
import shutil
import hashlib
from typing import Dict, Set, List
from dataclasses import dataclass

@dataclass
class SymbolMapping:
    name: str
    type_info: str
    file_id: str
    is_function: bool
    params: str = ""
    section: str = ""
    is_static: bool = False
    asm_label: str = ""

class SourceHarmonizerV73:
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")

        # Extended list of primitives and SDK base types
        self.immutables = {
            'bool', 'void', 'int', 'char', 'long', 'float', 'double',
            'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64',
            'size_t', 'uintptr_t', 'intptr_t', 'Mtx', 'Gfx', 'Vtx', 'ADPCM_STATE',
            'ALMicroTime', 'ALID', 'OSMesg', 'OSThread', 'OSYieldResult', 'u_long',
            'OSPri', 'u_short', 'u_char', 'OSId', 'u32*', 'uintptr_t', 'f32*'
        }
        self.conflict_registry: Set[str] = set()
        self.discovered_types: Set[str] = set()
        self.mappings: List[SymbolMapping] = []

    def get_file_id(self, filepath: str) -> str:
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:8]

    def setup_workspace(self):
        print("[>] Pass 0: Initializing Singularity-Stabilizer Workspace...")
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)

        # Copy files from decomp-files to Android project directory
        for sub in ["src", "include"]:
            src, dst = os.path.join(self.decomp_path, sub), os.path.join(self.android_path, sub)
            if os.path.exists(src):
                for root, _, files in os.walk(src):
                    rel = os.path.relpath(root, src)
                    target_dir = os.path.join(dst, rel)
                    os.makedirs(target_dir, exist_ok=True)
                    for f in files:
                        shutil.copy2(os.path.join(root, f), os.path.join(target_dir, f))

    def perform_introspection(self):
        print("[>] Pass 0.5: Executing Semantic Filtering (SDK Protection)...")
        # Patterns to identify and protect SDK symbols
        patterns = [
            re.compile(r'#define\s+([A-Za-z_]\w+)'),
            re.compile(r'typedef\s+.*?\s+(\w+);'),
            re.compile(r'\}\s*(\w+);'),
            re.compile(r'(?:struct|union|enum)\s+(\w+)'),
            re.compile(r'([A-Z][A-Z0-9_]+)\s*=\s*(?:0x)?[0-9A-Fa-f]+')
        ]
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                        for p in patterns:
                            self.conflict_registry.update(p.findall(content))
        print(f"    [Filtered] {len(self.conflict_registry)} SDK symbols protected from redefinition.")

    def harmonize_logic(self):
        print("[>] Pass 1 & 2: Weaving Stabilized Linkage...")
        # Patterns to identify types, functions, and data
        type_pat = re.compile(r'\b([A-Z][a-zA-Z0-9_]+)\b')
        func_pat = re.compile(r'^(static\s+)?(([\w\* ]+?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        data_pat = re.compile(r'^(static\s+)?([a-zA-Z_][\w\* ]+?)\s+([a-zA-Z_]\w*)\s*(?:=\s*([^;]+))?;', re.MULTILINE)

        # Process each C file
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                with open(path, 'r', errors='ignore') as file:
                    content = file.read()

                # Identify types
                for t in type_pat.findall(content):
                    if t not in self.conflict_registry and t not in self.immutables and not t.isupper():
                        self.discovered_types.add(t)

                # Replace function definitions
                def func_repl(m):
                    is_static = m.group(1) is not None
                    name = m.group(4).strip()
                    if name in ('main', 'Entry') or name in self.conflict_registry:
                        return m.group(0)

                    params = re.sub(r'\s+', ' ', m.group(5).strip()) or "void"
                    label = f"SS_{'S' if is_static else 'G'}_{fid}_{name}"
                    self.mappings.append(SymbolMapping(name, m.group(3).strip(), fid, True, params, ".text", is_static, label))

                    return f"\n#undef {name}\n__attribute__((used, visibility(\"protected\"))) {m.group(2).replace(name, f'{name} __asm__(\"{label}\")', 1)} "

                # Replace data definitions
                def data_repl(m):
                    is_static = m.group(1) is not None
                    dtype = m.group(2).strip()
                    name = m.group(3).strip()
                    value = m.group(4)

                    if name in self.conflict_registry or "extern" in dtype:
                        return m.group(0)

                    section = ".bss" if value is None else ".data"
                    if "const" in dtype:
                        section = ".rodata"

                    label = f"SS_{'S' if is_static else 'G'}_{fid}_{name}"
                    self.mappings.append(SymbolMapping(name, dtype, fid, False, "", section, is_static, label))

                    attr = f"__attribute__((used, section(\"{section}\"), visibility(\"protected\")))"
                    return f"\n#undef {name}\n{attr} {m.group(0).replace(name, f'{name} __asm__(\"{label}\")', 1)}"

                # Apply replacements
                patched = re.sub(func_pat, func_repl, content)
                patched = re.sub(data_pat, data_repl, patched)

                # Write patched content back to file
                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_artifacts(self):
        print("[>] Pass 3: Finalizing Stabilized Artifacts...")
        # Generate the harmonized_globals.h file
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n#include <ultra64.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")

            # Add opaque type definitions
            for t in sorted(self.discovered_types):
                f.write(f"#if !defined({t}_DEFINED) && !defined({t})\n  typedef struct {t} {t};\n  #define {t}_DEFINED\n#endif\n")

            # Add global linkage declarations
            for m in self.mappings:
                if m.is_static: continue
                f.write(f"#undef {m.name}\n")
                if m.is_function:
                    f.write(f"extern {m.type_info} {m.name}({m.params}) __asm__(\"{m.asm_label}\");\n")
                else:
                    f.write(f"extern {m.type_info} {m.name} __asm__(\"{m.asm_label}\");\n")
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

        # Generate the symbol map
        map_path = os.path.join(self.android_path, "symbol_map.txt")
        with open(map_path, 'w') as f:
            f.write("{\n  global:\n")
            for m in self.mappings:
                if not m.is_static:
                    f.write(f"    {m.asm_label};\n")
            f.write("  local: *;\n};")

    def run(self):
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v73.0 SINGULARITY-STABILIZER")
        print("="*60)
        self.setup_workspace()
        self.perform_introspection()
        self.harmonize_logic()
        self.generate_artifacts()
        print("\n" + "="*60)
        print(f"✓ STABILIZATION COMPLETE: {len(self.mappings)} Symbols Weaved")
        print("="*60 + "\n")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV73("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()