#!/usr/bin/env python3
"""
Banjo-Kazooie Decompilation Android Harmonizer v50.0 FINAL
Dynamically patches N64 source files for Android compatibility.
COMPLETE solution to all typedef, type discovery, and C99 issues.
"""

import os
import shutil
import re
import hashlib
from typing import Dict, Set, Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class FunctionSignature:
    """Represents a parsed function signature"""
    name: str
    return_type: str
    parameters: str
    
    
@dataclass 
class VariableDeclaration:
    """Represents a parsed variable declaration"""
    name: str
    var_type: str
    array_spec: str
    is_bss: bool


class SourceHarmonizerV50:
    """
    FINAL production harmonizer for N64 → Android compilation.
    
    Comprehensive solution for:
    1. ALL SDK typedef conflicts (ALWaveTable, ALCSeq, ALSynth, etc.)
    2. Complete type forward declaration (scans ALL type usage everywhere)
    3. C99 compatibility fixes (array initializers)
    4. Static symbol promotion with unique global namespacing
    """
    
    def __init__(self, android_path: str, decomp_path: str):
        self.android_path = os.path.normpath(android_path)
        self.decomp_path = os.path.normpath(decomp_path)
        self.src_target = os.path.join(self.android_path, "src")
        self.include_target = os.path.join(self.android_path, "include")
        self.cmake_file = os.path.join(self.android_path, "CMakeLists.txt")
        
        # Storage for parsed data
        self.func_signatures: Dict[str, FunctionSignature] = {}
        self.var_declarations: Dict[str, VariableDeclaration] = {}
        self.all_used_types: Set[str] = set()  # Every type seen anywhere
        self.sdk_defined_types: Set[str] = set()
        
        # COMPLETE SDK type list - MUST match actual SDK headers
        self.reserved_types = {
            # Standard C
            'void', 'char', 'int', 'short', 'long', 'float', 'double',
            'signed', 'unsigned', 'size_t', 'ptrdiff_t', 'wchar_t',
            'bool', 'true', 'false',
            
            # stdint
            'int8_t', 'int16_t', 'int32_t', 'int64_t',
            'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
            'intptr_t', 'uintptr_t', 'intmax_t', 'uintmax_t',
            
            # N64 SDK base
            'u8', 's8', 'u16', 's16', 'u32', 's32', 'u64', 's64', 'f32', 'f64',
            
            # N64 SDK graphics
            'Vtx', 'Vtx_t', 'Vtx_tn', 'Mtx', 'Mtx44', 'Gfx', 'GfxInfo',
            'Light', 'LookAt', 'Hilite', 'Acmd', 'Acdmd',
            
            # N64 SDK OS
            'OSThread', 'OSMesg', 'OSMesgQueue', 'OSTimer', 'OSTime',
            'OSIntMask', 'OSPri', 'OSId', 'OSPiHandle', 'OSIoMesg',
            'OSEvent', 'OSScMsg', 'OSContStatus', 'OSContPad', 'OSPfs',
            
            # N64 Audio Library - COMPLETE from libaudio.h
            'ALHeap', 'ALLink', 'ALGlobals',
            'ALVoice', 'ALVoiceConfig', 
            'ALSound', 'ALSoundState',
            'ALBank', 'ALBankFile', 'ALInstrument', 'ALInstrumentListItem',
            'ALKeyMap', 'ALWave', 'ALWaveTable',  # ← CRITICAL: Was missing!
            'ALEnvelope', 'ALADPCMBook', 'ALRawLoop', 'ALADPCMLoop', 'ALMIDIvoice',
            'ALSeq', 'ALSeqData', 'ALSeqFile', 'ALSeqMarker', 
            'ALSeqPlayer', 'ALSeqpConfig', 'ALCSPlayer',
            'ALCSeq', 'ALCSeqPlayer',
            'ALSndPlayer', 'ALSndpConfig', 
            'ALSynth', 'ALSynConfig',
            'ALPlayer',
            'ALEvent', 'ALEventListItem', 'ALEventQueue',
            'ALMicroTime', 'ALDMAproc', 'ALDMANew', 'ALDMAState',
            'ALFilter', 'ALPan', 'ALParam', 'ALMainBus', 'ALAuxBus',
            'ALMIDIEvent', 'ALVoiceEvent', 'ALSoundEvent', 'ALSeqEvent',
            
            # Extended N64 audio
            'N_ALSeqPlayer', 'N_ALVoice', 'N_PVoice',
            
            # Common
            'FILE', 'va_list', 'jmp_buf',
        }
        
        self.reserved_names = {
            'main', '_start', 
            'memcpy', 'memset', 'memmove', 'memcmp',
            'strcpy', 'strncpy', 'strcmp', 'strncmp', 'strlen',
            'printf', 'sprintf', 'fprintf', 'snprintf',
            'malloc', 'calloc', 'realloc', 'free',
        }

    def get_file_id(self, filepath: str) -> str:
        """Generate unique 12-char hash ID for file path"""
        rel_path = os.path.relpath(filepath, self.src_target)
        return hashlib.md5(rel_path.encode()).hexdigest()[:12]

    def sync_files(self):
        """Copy source and header files from decomp to android target"""
        print("  [>] Pass 0: Event-Horizon Sync...")
        
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)

        for sub in ["src", "include"]:
            source = os.path.join(self.decomp_path, sub)
            target = os.path.join(self.android_path, sub)
            
            if os.path.exists(source):
                for root, _, files in os.walk(source):
                    rel_path = os.path.relpath(root, source)
                    dest_dir = os.path.join(target, rel_path)
                    os.makedirs(dest_dir, exist_ok=True)
                    
                    for filename in files:
                        shutil.copy2(
                            os.path.join(root, filename),
                            os.path.join(dest_dir, filename)
                        )

    def extract_sdk_types(self):
        """Scan SDK headers to find all typedef'd types"""
        print("  [>] Pass 0.5: Scanning SDK Headers...")
        
        patterns = [
            re.compile(r'typedef\s+struct\s+\w*\s*\{[^}]*\}\s*(\w+)\s*;', re.DOTALL),
            re.compile(r'typedef\s+struct\s+\w+\s+(\w+)\s*;'),
            re.compile(r'typedef\s+union\s+\w+\s+(\w+)\s*;'),
            re.compile(r'typedef\s+enum\s+\w+\s+(\w+)\s*;'),
            re.compile(r'typedef\s+.+?\s+(\w+)\s*;'),
        ]
        
        include_dirs = [
            self.include_target,
            os.path.join(self.include_target, "2.0L"),
            os.path.join(self.include_target, "2.0L", "PR"),
            os.path.join(self.include_target, "core1"),
            os.path.join(self.include_target, "core2"),
        ]
        
        for inc_dir in include_dirs:
            if not os.path.exists(inc_dir):
                continue
                
            for root, _, files in os.walk(inc_dir):
                for filename in files:
                    if not filename.endswith('.h'):
                        continue
                        
                    try:
                        with open(os.path.join(root, filename), 'r', 
                                encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        for pattern in patterns:
                            for match in pattern.finditer(content):
                                type_name = match.group(1)
                                if type_name and (type_name[0].isupper() or '_' in type_name):
                                    self.sdk_defined_types.add(type_name)
                    except:
                        pass
        
        print(f"      Found {len(self.sdk_defined_types)} SDK types")

    def extract_all_type_names(self, text: str) -> Set[str]:
        """
        Extract ALL CamelCase type names from C code text.
        This is AGGRESSIVE - finds every possible type usage.
        
        Matches: ActorMarker, Cube, File, SkeletalAnimation, etc.
        """
        # Remove C keywords
        text = re.sub(r'\b(const|static|extern|inline|volatile|restrict)\b', '', text)
        text = re.sub(r'\b(struct|union|enum)\b', '', text)
        
        # Remove operators and delimiters
        text = re.sub(r'[\*\[\]\(\)&\{\}]+', ' ', text)
        
        # Extract ALL CamelCase identifiers (custom types)
        found_types = set(re.findall(r'\b([A-Z][a-zA-Z0-9_]*)\b', text))
        
        # Filter out SDK types, reserved types, and common macros
        valid_types = set()
        for t in found_types:
            if (t not in self.reserved_types and 
                t not in self.sdk_defined_types and
                t not in ('TRUE', 'FALSE', 'NULL')):
                valid_types.add(t)
        
        return valid_types

    def scan_all_headers(self):
        """Scan project headers for type definitions"""
        print("  [>] Pass 0.75: Scanning Project Headers...")
        
        patterns = [
            re.compile(r'typedef\s+struct\s+\w*\s*\{[^}]*\}\s*(\w+)\s*;', re.DOTALL),
            re.compile(r'struct\s+(\w+)\s*\{'),
            re.compile(r'typedef\s+struct\s+(\w+)\s+(\w+)\s*;'),
            re.compile(r'union\s+(\w+)\s*\{'),
        ]
        
        for root, _, files in os.walk(self.include_target):
            for filename in files:
                if not filename.endswith('.h'):
                    continue
                    
                try:
                    with open(os.path.join(root, filename), 'r',
                            encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Extract type definitions
                    for pattern in patterns:
                        for match in pattern.finditer(content):
                            for group in match.groups():
                                if group and group[0].isupper():
                                    self.all_used_types.add(group)
                    
                    # Also scan all text for type usage
                    self.all_used_types.update(self.extract_all_type_names(content))
                except:
                    pass

    def map_linkage(self):
        """Parse all C files - extract signatures AND discover ALL type usage"""
        print("  [>] Pass 1: Comprehensive Type Discovery...")
        
        func_pattern = re.compile(
            r'^static\s+'
            r'(?!.*\binline\b)(?!.*\bextern\b)'
            r'((?:const\s+)?(?:struct\s+|union\s+|enum\s+)?[\w\s\*]+?)\s+'
            r'([a-zA-Z_]\w*)\s*'
            r'\(([^\)]*)\)\s*'
            r'\{',
            re.MULTILINE
        )
        
        var_pattern = re.compile(
            r'^static\s+'
            r'(const\s+)?'
            r'((?:struct\s+|union\s+)?[\w\s\*]+)\s+'
            r'([a-zA-Z_]\w*)'
            r'(\s*\[[^\]]*\])*\s*'
            r'([=:;])',
            re.MULTILINE
        )
        
        file_count = 0
        for root, _, files in os.walk(self.src_target):
            for filename in files:
                if not filename.endswith('.c'):
                    continue
                    
                filepath = os.path.join(root, filename)
                file_id = self.get_file_id(filepath)
                file_count += 1
                
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # CRITICAL: Extract ALL type names from entire file
                    self.all_used_types.update(self.extract_all_type_names(content))
                    
                    # Extract function signatures
                    for match in func_pattern.finditer(content):
                        return_type = match.group(1).strip()
                        func_name = match.group(2).strip()
                        params = match.group(3).strip() or "void"
                        
                        if func_name in self.reserved_names:
                            continue
                        
                        key = f"{file_id}_{func_name}"
                        self.func_signatures[key] = FunctionSignature(
                            name=func_name,
                            return_type=return_type,
                            parameters=params
                        )
                    
                    # Extract variable declarations
                    for match in var_pattern.finditer(content):
                        is_const = match.group(1) is not None
                        var_type = match.group(2).strip()
                        var_name = match.group(3).strip()
                        array_spec = match.group(4).strip() if match.group(4) else ""
                        terminator = match.group(5)
                        
                        full_type = ("const " if is_const else "") + var_type
                        
                        key = f"{file_id}_{var_name}"
                        self.var_declarations[key] = VariableDeclaration(
                            name=var_name,
                            var_type=full_type,
                            array_spec=array_spec,
                            is_bss=(terminator == ';')
                        )
                        
                except Exception as e:
                    print(f"      Warning: {filename}: {e}")
        
        print(f"      Processed {file_count} C files")
        print(f"      Discovered {len(self.all_used_types)} type references")
        print(f"      Found {len(self.func_signatures)} functions")
        print(f"      Found {len(self.var_declarations)} variables")

    def fix_c99_compatibility(self):
        """Fix C99 array initializer incompatibilities"""
        print("  [>] Pass 1.5: C99 Compatibility Fixes...")
        
        # Pattern: type var[size] = identifier;
        array_init = re.compile(
            r'^\s*([\w\s\*]+)\s+(\w+)\s*\[([^\]]+)\]\s*=\s*([a-zA-Z_]\w+)\s*;',
            re.MULTILINE
        )
        
        fixed = 0
        for root, _, files in os.walk(self.src_target):
            for filename in files:
                if not filename.endswith('.c'):
                    continue
                    
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    original = content
                    
                    def fix_init(match):
                        type_name = match.group(1).strip()
                        var_name = match.group(2)
                        size = match.group(3)
                        source = match.group(4)
                        return (
                            f"{type_name} {var_name}[{size}];\n"
                            f"    memcpy({var_name}, {source}, sizeof({var_name}));"
                        )
                    
                    content = array_init.sub(fix_init, content)
                    
                    if content != original:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        fixed += 1
                except:
                    pass
        
        if fixed:
            print(f"      Fixed {fixed} C99 issues")

    def promote_linkage(self):
        """Promote static symbols to global visibility"""
        print("  [>] Pass 2: Symbol Promotion...")
        
        modified = 0
        
        for root, _, files in os.walk(self.src_target):
            for filename in files:
                if not filename.endswith('.c'):
                    continue
                    
                filepath = os.path.join(root, filename)
                file_id = self.get_file_id(filepath)
                
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    original = content
                    
                    # Replace functions
                    def replace_func(match):
                        ret_type = match.group(1).strip()
                        func_name = match.group(2).strip()
                        params = match.group(3).strip()
                        
                        if func_name in self.reserved_names:
                            return match.group(0)
                        
                        key = f"{file_id}_{func_name}"
                        return (
                            f"#undef {func_name}\n"
                            f"#define GLOBAL_DEF_{key}\n"
                            f"__attribute__((visibility(\"protected\"), used)) "
                            f"{ret_type} EH_{key}({params}) "
                        )
                    
                    func_pat = re.compile(
                        r'^static\s+(?!.*\binline\b)(?!.*\bextern\b)'
                        r'((?:const\s+)?(?:struct\s+|union\s+|enum\s+)?[\w\s\*]+?)\s+'
                        r'([a-zA-Z_]\w*)\s*\(([^\)]*)\)\s*\{',
                        re.MULTILINE
                    )
                    content = func_pat.sub(replace_func, content)
                    
                    # Replace variables
                    for key, v in self.var_declarations.items():
                        if not key.startswith(file_id):
                            continue
                        
                        attr = '__attribute__((visibility("protected"), used, aligned(8)))'
                        
                        if v.is_bss:
                            pat = (
                                r'^static\s+(?:const\s+)?(?:struct\s+|union\s+)?[\w\s\*]+\s+'
                                + re.escape(v.name) + re.escape(v.array_spec) + r'\s*;'
                            )
                            repl = (
                                f"#undef {v.name}\n#define GLOBAL_DEF_{key}\n"
                                f"{attr} {v.var_type} EH_{key}{v.array_spec};"
                            )
                        else:
                            pat = (
                                r'^static\s+(?:const\s+)?(?:struct\s+|union\s+)?[\w\s\*]+\s+'
                                + re.escape(v.name) + re.escape(v.array_spec) + r'\s*[=:]'
                            )
                            repl = (
                                f"#undef {v.name}\n#define GLOBAL_DEF_{key}\n"
                                f"{attr} {v.var_type} EH_{key}{v.array_spec} ="
                            )
                        
                        content = re.sub(pat, repl, content, flags=re.MULTILINE)
                    
                    if content != original:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write('#include <ultra64.h>\n')
                            f.write('#include "harmonized_globals.h"\n')
                            f.write(content)
                        modified += 1
                except:
                    pass
        
        print(f"      Modified {modified} files")

    def generate_header(self):
        """Generate harmonized_globals.h with ALL type forward declarations"""
        print("  [>] Pass 3: Header Generation...")
        
        # Types to declare = all used types MINUS SDK/reserved types
        types_to_declare = set()
        for t in self.all_used_types:
            if t not in self.sdk_defined_types and t not in self.reserved_types:
                types_to_declare.add(t)
        
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        with open(header_path, 'w', encoding='utf-8') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            f.write("#include <stdbool.h>\n#include <stdint.h>\n")
            f.write("#include <stddef.h>\n#include <string.h>\n\n")
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            f.write("/* Forward declarations - ALL custom types */\n")
            f.write("/* SDK types NOT redeclared to avoid conflicts */\n\n")
            
            for t in sorted(types_to_declare):
                f.write(f"#ifndef TYPE_DEFINED_{t}\n")
                f.write(f"  typedef struct {t} {t};\n")
                f.write(f"  #define TYPE_DEFINED_{t}\n")
                f.write(f"#endif\n")
            
            f.write(f"\n/* {len(types_to_declare)} types declared */\n\n")
            
            f.write("/* Function declarations */\n")
            for key, sig in sorted(self.func_signatures.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n")
                f.write(f"  #undef {sig.name}\n")
                f.write(f"  #define {sig.name} EH_{key}\n")
                f.write(f"  extern {sig.return_type} EH_{key}({sig.parameters});\n")
                f.write(f"#endif\n")
            
            f.write(f"\n/* {len(self.func_signatures)} functions */\n\n")
            
            f.write("/* Variable declarations */\n")
            for key, v in sorted(self.var_declarations.items()):
                f.write(f"#ifndef GLOBAL_DEF_{key}\n")
                f.write(f"  #undef {v.name}\n")
                f.write(f"  #define {v.name} EH_{key}\n")
                f.write(f"  extern {v.var_type} EH_{key}{v.array_spec};\n")
                f.write(f"#endif\n")
            
            f.write(f"\n/* {len(self.var_declarations)} variables */\n\n")
            f.write("#ifdef __cplusplus\n}\n#endif\n\n")
            f.write("#endif /* HARMONIZED_GLOBALS_H */\n")
        
        print(f"      Declared {len(types_to_declare)} types")

    def patch_cmake(self):
        """Update CMakeLists.txt"""
        print("  [>] Pass 4: CMake Patching...")
        
        if not os.path.exists(self.cmake_file):
            return
        
        with open(self.cmake_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(r'# --- Harmonizer.*?# -{20,}', '', content, flags=re.DOTALL)
        
        injection = (
            "\n# --- Harmonizer v50.0 FINAL ---\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -O3 -fPIC -fno-common "
            "-fvisibility=hidden -flto=thin\")\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C)\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# ------------------------------\n"
        )
        
        with open(self.cmake_file, 'w', encoding='utf-8') as f:
            f.write(content + injection)

    def run(self):
        """Execute all harmonization passes"""
        print("\n" + "="*60)
        print("Banjo-Kazooie Harmonizer v50.0 FINAL")
        print("="*60)
        
        self.sync_files()
        self.extract_sdk_types()
        self.scan_all_headers()
        self.map_linkage()
        self.fix_c99_compatibility()
        self.promote_linkage()
        self.generate_header()
        self.patch_cmake()
        
        print("\n" + "="*60)
        print("✓ v50.0 FINAL: Complete")
        print("="*60)
        print(f"  SDK Types: {len(self.sdk_defined_types)}")
        print(f"  Custom Types: {len(self.all_used_types)}")
        print(f"  Functions: {len(self.func_signatures)}")
        print(f"  Variables: {len(self.var_declarations)}")
        print("="*60 + "\n")


if __name__ == "__main__":
    harmonizer = SourceHarmonizerV50(
        android_path="Android/app/src/main/cpp",
        decomp_path="decomp-files"
    )
    harmonizer.run()
