#!/usr/bin/env python3
import os
import re
import shutil
import hashlib
from typing import Set, List, Dict
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

        self.c_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 
            'do', 'break', 'continue', 'case', 'default', 'goto', 'struct', 
            'union', 'enum', 'static', 'extern', 'const', 'volatile', 'inline',
            'register', 'restrict', 'auto', 'void', 'int', 'char', 'float', 'double',
            'short', 'long', 'signed', 'unsigned', 'typedef'
        }

        self.immutables = {
            'bool', 'u8', 'u16', 'u32', 'u64', 's8', 's16', 's32', 's64', 'f32', 'f64',
            'size_t', 'uintptr_t', 'intptr_t', 'Mtx', 'Gfx', 'Vtx', 'ADPCM_STATE',
            'ALMicroTime', 'ALID', 'OSMesg', 'OSThread', 'OSYieldResult', 'u_long',
            'OSPri', 'u_short', 'u_char', 'OSId', 'u32*', 'uintptr_t', 'f32*',
            'ALDMANew', 'ALFxRef', 'ALVoiceHandler', 'CartRomHandle', 'LeoDiskHandle',
            'AL_MIDI_ChannelMask', 'AL_MIDI_ChannelModeSelect', 'AL_MIDI_ChannelPressure',
            'AL_MIDI_ControlChange', 'AL_MIDI_Meta', 'AL_MIDI_NoteOff', 'AL_MIDI_NoteOn',
            'AL_MIDI_PitchBendChange', 'AL_MIDI_PolyKeyPressure', 'AL_MIDI_ProgramChange',
            'AL_MIDI_StatusMask', 'OSMesgQueue', 'OSIoMesg', 'OSContStatus', 'OSContPad'
        }
        
        self.conflict_registry: Set[str] = set()
        self.discovered_types: Set[str] = set()
        
        # Structural Registries
        self.mappings: List[SymbolMapping] = []
        self.global_symbols: Dict[str, SymbolMapping] = {}
        self.all_symbol_names: Set[str] = set()

    def get_file_id(self, filepath: str) -> str:
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:8]

    def remove_comments(self, text: str) -> str:
        # Strip block comments
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        # Strip line comments
        text = re.sub(r'//.*', '', text)
        return text

    def setup_workspace(self):
        print("[>] Pass 0: Initializing Singularity-Stabilizer Workspace...")
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)

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
        patterns = [
            re.compile(r'#define\s+([A-Za-z_]\w+)'),
            re.compile(r'typedef\s+.*?\s+(\w+);'),
            re.compile(r'\}\s*(\w+);'),
            re.compile(r'(?:struct|union|enum)\s+(\w+)'),
            re.compile(r'([A-Za-z_]\w+)\s*=\s*(?:0x)?[0-9A-Fa-f]+'),
            re.compile(r'typedef\s+[\w\s\*]+\(\s*\*\s*([A-Za-z_]\w+)\s*\)')
        ]
        for root, _, files in os.walk(self.include_target):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = self.remove_comments(f.read())
                        for p in patterns:
                            self.conflict_registry.update(p.findall(content))
        print(f"    [Filtered] {len(self.conflict_registry)} SDK symbols protected from redefinition.")

    def harmonize_logic(self):
        print("[>] Pass 1 & 2: Weaving Stabilized Linkage...")
        
        func_pat = re.compile(r'^(static\s+)?(([a-zA-Z_][\w\* ]{0,60}?)\s+([a-zA-Z_]\w*)\s*\(([^\{]*?)\))\s*\{', re.MULTILINE | re.DOTALL)
        data_pat = re.compile(r'^(static\s+)?([a-zA-Z_][\w\* ]{0,60}?)\s+([a-zA-Z_]\w*)\s*(?:=\s*([^;]+))?;', re.MULTILINE)

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if not f.endswith('.c'): continue
                path = os.path.join(root, f)
                fid = self.get_file_id(path)
                
                with open(path, 'r', errors='ignore') as file:
                    content = self.remove_comments(file.read())

                def func_repl(m):
                    is_static = m.group(1) is not None
                    static_str = "static " if is_static else ""
                    ret_type = " ".join(m.group(3).split())
                    name = m.group(4).strip()
                    params = m.group(5).strip() or "void"
                    
                    # Safe exit for Keywords/SDK
                    if name in self.c_keywords or name in ('main', 'Entry') or name in self.conflict_registry:
                        return m.group(0)

                    # Extract Types from Parameters (Catches ActorMarker, Struct5Fs, etc.)
                    for word in re.findall(r'\b([a-zA-Z_]\w+)\b', params + " " + ret_type):
                        if word not in self.c_keywords and word not in self.immutables:
                            self.discovered_types.add(word)

                    label = f"SS_{'S' if is_static else 'G'}_{fid}_{name}"
                    mapping = SymbolMapping(name, ret_type, fid, True, params, ".text", is_static, label)
                    
                    self.all_symbol_names.add(name)
                    # FIRST-WIN POLICY: Only keep the first signature we find for global functions
                    if not is_static and name not in self.global_symbols:
                        self.global_symbols[name] = mapping
                    
                    self.mappings.append(mapping)
                    
                    # Exact C Reconstruction (Eliminates regex replace bugs)
                    return f"\n#undef {name}\n__attribute__((used, visibility(\"protected\"))) {static_str}{ret_type} {name} __asm__(\"{label}\")({params}) {{"

                def data_repl(m):
                    is_static = m.group(1) is not None
                    static_str = "static " if is_static else ""
                    dtype = " ".join(m.group(2).split())
                    name = m.group(3).strip()
                    value = m.group(4)

                    if name in self.c_keywords or name in self.conflict_registry or "extern" in dtype:
                        return m.group(0)

                    for word in re.findall(r'\b([a-zA-Z_]\w+)\b', dtype):
                        if word not in self.c_keywords and word not in self.immutables:
                            self.discovered_types.add(word)

                    section = ".bss" if value is None else ".data"
                    if "const" in dtype: section = ".rodata"

                    label = f"SS_{'S' if is_static else 'G'}_{fid}_{name}"
                    mapping = SymbolMapping(name, dtype, fid, False, "", section, is_static, label)
                    
                    self.all_symbol_names.add(name)
                    # FIRST-WIN POLICY for Data
                    if not is_static and name not in self.global_symbols:
                        self.global_symbols[name] = mapping
                        
                    self.mappings.append(mapping)

                    attr = f"__attribute__((used, section(\"{section}\"), visibility(\"protected\")))"
                    if value is not None:
                        return f"\n#undef {name}\n{attr} {static_str}{dtype} {name} __asm__(\"{label}\") = {value};"
                    else:
                        return f"\n#undef {name}\n{attr} {static_str}{dtype} {name} __asm__(\"{label}\");"

                patched = re.sub(func_pat, func_repl, content)
                patched = re.sub(data_pat, data_repl, patched)

                with open(path, 'w') as file:
                    file.write('#include <ultra64.h>\n#include "harmonized_globals.h"\n' + patched)

    def generate_artifacts(self):
        print("[>] Pass 3: Finalizing Stabilized Artifacts...")
        
        # Anti-Collision Math: Remove function/variable names from Type list
        clean_types = self.discovered_types - self.all_symbol_names - self.conflict_registry - self.c_keywords - self.immutables

        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n#include <ultra64.h>\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")

            # Output Forward Declarations FIRST
            for t in sorted(clean_types):
                if not t[0].isdigit(): # Safety block against 1st, 2nd, etc.
                    f.write(f"#if !defined({t}_DEFINED) && !defined({t})\n  typedef struct {t} {t};\n  #define {t}_DEFINED\n#endif\n")

            f.write("\n")

            # Output exactly ONE declaration per global symbol
            for name, m in self.global_symbols.items():
                f.write(f"#undef {name}\n")
                if m.is_function:
                    f.write(f"extern {m.type_info} {name}({m.params}) __asm__(\"{m.asm_label}\");\n")
                else:
                    f.write(f"extern {m.type_info} {name} __asm__(\"{m.asm_label}\");\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

        map_path = os.path.join(self.android_path, "symbol_map.txt")
        with open(map_path, 'w') as f:
            f.write("{\n  global:\n")
            for m in self.mappings:
                if not m.is_static:
                    f.write(f"    {m.asm_label};\n")
            f.write("  local: *;\n};")

    def run(self):
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v73.2 SINGULARITY-STABILIZER (ENHANCED)")
        print("="*60)
        self.setup_workspace()
        self.perform_introspection()
        self.harmonize_logic()
        self.generate_artifacts()
        print("\n" + "="*60)
        print(f"✓ STABILIZATION COMPLETE: {len(self.global_symbols)} Globals / {len(self.mappings)} Total Weaved")
        print("="*60 + "\n")

if __name__ == "__main__":
    harmonizer = SourceHarmonizerV73("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
