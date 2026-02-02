#!/usr/bin/env python3
"""
Banjo-Kazooie Decompilation Android Harmonizer v49.0 FINAL
Dynamically patches N64 source files for Android compatibility.
Handles all type discovery, SDK conflicts, and C99 compatibility issues.
"""

import os
import shutil
import re
import hashlib
from typing import Dict, Set, Tuple, Optional, List
from dataclasses import dataclass
from pathlib import Path


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


class SourceHarmonizerV49:
    """
    Final production harmonizer for N64 decompiled source files.
    
    Solves all known issues:
    1. SDK typedef conflicts (ALWaveTable, ALCSeq, etc.)
    2. Forward declaration of ALL custom types used in parameters
    3. C99 array initializer compatibility fixes
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
        self.all_used_types: Set[str] = set()  # ALL types seen anywhere
        self.sdk_defined_types: Set[str] = set()
        
        # Comprehensive SDK types - MUST be kept in sync with actual SDK headers
        self.reserved_types = {
            # Standard C types
            'void', 'char', 'int', 'short', 'long', 'float', 'double',
            'signed', 'unsigned', 'size_t', 'ptrdiff_t', 'wchar_t',
            'bool', 'true', 'false',
            
            # stdint types
            'int8_t', 'int16_t', 'int32_t', 'int64_t',
            'uint8_t', 'uint16_t', 'uint32_t', 'uint64_t',
            'intptr_t', 'uintptr_t', 'intmax_t', 'uintmax_t',
            
            # N64 SDK base types
            'u8', 's8', 'u16', 's16', 'u32', 's32', 'u64', 's64',
            'f32', 'f64',
            
            # N64 SDK graphics types
            'Vtx', 'Vtx_t', 'Vtx_tn', 'Mtx', 'Mtx44', 'Gfx', 'GfxInfo',
            'Light', 'LookAt', 'Hilite', 'Acmd', 'Acdmd',
            
            # N64 SDK OS types  
            'OSThread', 'OSMesg', 'OSMesgQueue', 'OSTimer', 'OSTime',
            'OSIntMask', 'OSPri', 'OSId', 'OSPiHandle', 'OSIoMesg',
            'OSEvent', 'OSScMsg', 'OSContStatus', 'OSContPad', 'OSPfs',
            
            # N64 Audio Library - COMPLETE list from libaudio.h
            'ALHeap', 'ALLink', 'ALGlobals',
            'ALVoice', 'ALVoiceConfig', 
            'ALSound', 'ALSoundState',
            'ALBank', 'ALBankFile', 'ALInstrument', 'ALInstrumentListItem',
            'ALKeyMap', 'ALWave', 'ALWaveTable',  # CRITICAL: ALWaveTable was missing!
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
            
            # Extended N64 audio (internal)
            'N_ALSeqPlayer', 'N_ALVoice', 'N_PVoice',
            
            # Common utility types
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
        """Generate a unique 12-character hash ID for a file path"""
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
                        src_file = os.path.join(root, filename)
                        dst_file = os.path.join(dest_dir, filename)
                        shutil.copy2(src_file, dst_file)

    def extract_sdk_types(self):
        """
        Scan SDK headers to identify all typedef'd types.
        This is CRITICAL to prevent typedef redefinition errors.
        """
        print("  [>] Pass 0.5: Scanning SDK Headers for Type Conflicts...")
        
        # Enhanced patterns to catch all typedef forms
        patterns = [
            # typedef struct X_s { ... } X;
            re.compile(r'typedef\s+struct\s+\w*\s*\{[^}]*\}\s*(\w+)\s*;', re.DOTALL),
            # typedef struct X Y;
            re.compile(r'typedef\s+struct\s+\w+\s+(\w+)\s*;'),
            # typedef union X Y;
            re.compile(r'typedef\s+union\s+\w+\s+(\w+)\s*;'),
            # typedef enum X Y;
            re.compile(r'typedef\s+enum\s+\w+\s+(\w+)\s*;'),
            # typedef ... Y;
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
                        
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        for pattern in patterns:
                            for match in pattern.finditer(content):
                                type_name = match.group(1)
                                # Only add if it looks like a type (CamelCase or ALL_CAPS)
                                if type_name and (type_name[0].isupper() or '_' in type_name):
                                    self.sdk_defined_types.add(type_name)
                                    
                    except Exception as e:
                        pass  # Silently skip problematic files
        
        print(f"      Found {len(self.sdk_defined_types)} SDK-defined types")

    def extract_all_types(self, text: str) -> List[str]:
        """
        Extract ALL type names from C code text.
        This is more aggressive - we want to find every possible type usage.
        
        Extracts from:
        - Return types
        - Parameter types
        - Variable types
        - Pointer types
        - Array element types
        - struct/union/enum references
        """
        # Remove C keywords and qualifiers
        text = re.sub(r'\b(const|static|extern|inline|volatile|restrict|auto|register)\b', '', text)
        text = re.sub(r'\b(struct|union|enum)\b', '', text)
        
        # Remove pointer/array/parenthesis notation to isolate type names
        text = re.sub(r'[\*\[\]\(\)]+', ' ', text)
        
        # Extract all CamelCase or mixed-case identifiers
        # This catches: ActorMarker, Cube, File, NodeProp, etc.
        types = re.findall(r'\b([A-Z][a-zA-Z0-9_]*)\b', text)
        
        # Filter out reserved types and SDK types
        valid_types = []
        for t in types:
            if (t not in self.reserved_types and 
                t not in self.sdk_defined_types and
                t not in ('TRUE', 'FALSE', 'NULL')):  # Common macros
                valid_types.append(t)
        
        return valid_types

    def scan_headers_for_types(self):
        """
        Scan all header files to find struct/typedef declarations.
        This discovers types that are defined in headers but used in source.
        """
        print("  [>] Pass 0.75: Scanning Project Headers for Type Definitions...")
        
        type_def_patterns = [
            # typedef struct X { ... } Y;
            re.compile(r'typedef\s+struct\s+\w*\s*\{[^}]*\}\s*(\w+)\s*;', re.DOTALL),
            # struct X { ... };
            re.compile(r'struct\s+(\w+)\s*\{'),
            # typedef struct X Y;
            re.compile(r'typedef\s+struct\s+(\w+)\s+(\w+)\s*;'),
            # union X { ... };
            re.compile(r'union\s+(\w+)\s*\{'),
        ]
        
        header_types = set()
        
        for root, _, files in os.walk(self.include_target):
            for filename in files:
                if not filename.endswith('.h'):
                    continue
                    
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for pattern in type_def_patterns:
                        for match in pattern.finditer(content):
                            # Get all groups and take non-None ones
                            for group in match.groups():
                                if group and group[0].isupper():
                                    header_types.add(group)
                                    
                except Exception:
                    pass
        
        # Add header types to all_used_types
        self.all_used_types.update(header_types)
        print(f"      Found {len(header_types)} types in project headers")

    def map_linkage(self):
        """
        Parse all C source files to extract function/variable info
        and discover ALL type usage.
        """
        print("  [>] Pass 1: Comprehensive Type Discovery & Mapping...")
        
        # Pattern for static function declarations
        func_pattern = re.compile(
            r'^static\s+'
            r'(?!.*\binline\b)(?!.*\bextern\b)'
            r'((?:const\s+)?(?:struct\s+|union\s+|enum\s+)?[\w\s\*]+?)\s+'
            r'([a-zA-Z_]\w*)\s*'
            r'\(([^\)]*)\)\s*'
            r'\{',
            re.MULTILINE
        )
        
        # Pattern for static variable declarations
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
                    
                    # Extract ALL type names from entire file content
                    # This catches types used anywhere - params, returns, casts, etc.
                    file_types = self.extract_all_types(content)
                    self.all_used_types.update(file_types)
                    
                    # Extract function signatures
                    for match in func_pattern.finditer(content):
                        return_type_raw = match.group(1).strip()
                        func_name = match.group(2).strip()
                        params_raw = match.group(3).strip() or "void"
                        
                        if func_name in self.reserved_names:
                            continue
                        
                        key = f"{file_id}_{func_name}"
                        self.func_signatures[key] = FunctionSignature(
                            name=func_name,
                            return_type=return_type_raw,
                            parameters=params_raw
                        )
                        
                        # Extract types from signature
                        sig_types = self.extract_all_types(f"{return_type_raw} {params_raw}")
                        self.all_used_types.update(sig_types)
                    
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
                        
                        # Extract types from variable type
                        var_types = self.extract_all_types(full_type)
                        self.all_used_types.update(var_types)
                        
                except Exception as e:
                    print(f"      Warning: Error processing {filename}: {e}")
        
        print(f"      Processed {file_count} C files")
        print(f"      Discovered {len(self.all_used_types)} total type references")
        print(f"      Found {len(self.func_signatures)} static functions")
        print(f"      Found {len(self.var_declarations)} static variables")

    def fix_c99_compatibility(self):
        """
        Fix C99 compatibility issues in source files.
        
        Specifically handles:
        - Array initializers that use variable names instead of array literals
          Example: u8 tmp[6] = array_var; -> memcpy(tmp, array_var, sizeof(tmp));
        """
        print("  [>] Pass 1.5: Fixing C99 Compatibility Issues...")
        
        fixed_count = 0
        
        # Pattern to match: type name[size] = identifier;
        # This is invalid in C99 - must use memcpy or explicit initialization
        array_init_pattern = re.compile(
            r'^\s*([\w\s\*]+)\s+(\w+)\s*\[([^\]]+)\]\s*=\s*([a-zA-Z_]\w+)\s*;',
            re.MULTILINE
        )
        
        for root, _, files in os.walk(self.src_target):
            for filename in files:
                if not filename.endswith('.c'):
                    continue
                    
                filepath = os.path.join(root, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    original = content
                    
                    # Replace invalid array initializers with memcpy
                    def replace_array_init(match):
                        type_name = match.group(1).strip()
                        var_name = match.group(2)
                        array_size = match.group(3)
                        source_var = match.group(4)
                        
                        # Generate replacement with memcpy
                        return (
                            f"{type_name} {var_name}[{array_size}];\n"
                            f"    memcpy({var_name}, {source_var}, sizeof({var_name}));"
                        )
                    
                    content = array_init_pattern.sub(replace_array_init, content)
                    
                    if content != original:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        fixed_count += 1
                        
                except Exception as e:
                    print(f"      Warning: Error fixing C99 in {filename}: {e}")
        
        if fixed_count > 0:
            print(f"      Fixed C99 issues in {fixed_count} files")

    def promote_linkage(self):
        """
        Transform static functions and variables to have global visibility.
        """
        print("  [>] Pass 2: Global Symbol Promotion...")
        
        modified_count = 0
        
        for root, _, files in os.walk(self.src_target):
            for filename in files:
                if not filename.endswith('.c'):
                    continue
                    
                filepath = os.path.join(root, filename)
                file_id = self.get_file_id(filepath)
                
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Replace static function definitions
                    def replace_func(match):
                        return_type = match.group(1).strip()
                        func_name = match.group(2).strip()
                        params = match.group(3).strip()
                        
                        if func_name in self.reserved_names:
                            return match.group(0)
                        
                        key = f"{file_id}_{func_name}"
                        
                        return (
                            f"#undef {func_name}\n"
                            f"#define GLOBAL_DEF_{key}\n"
                            f"__attribute__((visibility(\"protected\"), used)) "
                            f"{return_type} EH_{key}({params}) "
                        )
                    
                    func_pattern = re.compile(
                        r'^static\s+'
                        r'(?!.*\binline\b)(?!.*\bextern\b)'
                        r'((?:const\s+)?(?:struct\s+|union\s+|enum\s+)?[\w\s\*]+?)\s+'
                        r'([a-zA-Z_]\w*)\s*'
                        r'\(([^\)]*)\)\s*'
                        r'\{',
                        re.MULTILINE
                    )
                    
                    content = func_pattern.sub(replace_func, content)
                    
                    # Replace static variable definitions
                    for key, var_decl in self.var_declarations.items():
                        if not key.startswith(file_id):
                            continue
                        
                        var_name = var_decl.name
                        var_type = var_decl.var_type
                        array_spec = var_decl.array_spec
                        is_bss = var_decl.is_bss
                        
                        attr = '__attribute__((visibility("protected"), used, aligned(8)))'
                        
                        if is_bss:
                            pattern = (
                                r'^static\s+'
                                r'(?:const\s+)?'
                                r'(?:struct\s+|union\s+)?'
                                r'[\w\s\*]+\s+'
                                + re.escape(var_name)
                                + re.escape(array_spec)
                                + r'\s*;'
                            )
                            replacement = (
                                f"#undef {var_name}\n"
                                f"#define GLOBAL_DEF_{key}\n"
                                f"{attr} {var_type} EH_{key}{array_spec};"
                            )
                        else:
                            pattern = (
                                r'^static\s+'
                                r'(?:const\s+)?'
                                r'(?:struct\s+|union\s+)?'
                                r'[\w\s\*]+\s+'
                                + re.escape(var_name)
                                + re.escape(array_spec)
                                + r'\s*[=:]'
                            )
                            replacement = (
                                f"#undef {var_name}\n"
                                f"#define GLOBAL_DEF_{key}\n"
                                f"{attr} {var_type} EH_{key}{array_spec} ="
                            )
                        
                        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                    
                    # Only write if content changed
                    if content != original_content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            # Include SDK header first, then harmonized header
                            f.write('#include <ultra64.h>\n')
                            f.write('#include "harmonized_globals.h"\n')
                            f.write(content)
                        modified_count += 1
                        
                except Exception as e:
                    print(f"      Warning: Error promoting linkage in {filename}: {e}")
        
        print(f"      Modified {modified_count} source files")

    def generate_header(self):
        """
        Generate harmonized_globals.h with forward declarations.
        
        Key: Only declare types that are:
        1. Actually used (in all_used_types)
        2. NOT in SDK headers (sdk_defined_types)
        3. NOT primitive types (reserved_types)
        """
        print("  [>] Pass 3: Generating Comprehensive Header...")
        
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        # Determine which types need forward declaration
        types_to_declare = set()
        for type_name in self.all_used_types:
            if (type_name not in self.sdk_defined_types and
                type_name not in self.reserved_types):
                types_to_declare.add(type_name)
        
        with open(header_path, 'w', encoding='utf-8') as f:
            # Header guard
            f.write("#ifndef HARMONIZED_GLOBALS_H\n")
            f.write("#define HARMONIZED_GLOBALS_H\n\n")
            
            # Standard includes
            f.write("/* Standard library headers */\n")
            f.write("#include <stdbool.h>\n")
            f.write("#include <stdint.h>\n")
            f.write("#include <stddef.h>\n")
            f.write("#include <string.h>  /* for memcpy */\n\n")
            
            # C++ compatibility
            f.write("#ifdef __cplusplus\n")
            f.write("extern \"C\" {\n")
            f.write("#endif\n\n")
            
            # Forward declare ALL custom types
            f.write("/* ========================================\n")
            f.write(" * Forward declarations for ALL custom types\n")
            f.write(" * SDK types from ultra64.h/libaudio.h are NOT redeclared\n")
            f.write(" * ======================================== */\n\n")
            
            for type_name in sorted(types_to_declare):
                f.write(f"#ifndef TYPE_DEFINED_{type_name}\n")
                f.write(f"  typedef struct {type_name} {type_name};\n")
                f.write(f"  #define TYPE_DEFINED_{type_name}\n")
                f.write(f"#endif\n")
            
            f.write(f"\n/* {len(types_to_declare)} custom types declared */\n\n")
            
            # Function declarations
            f.write("/* ========================================\n")
            f.write(" * Harmonized function declarations\n")
            f.write(" * ======================================== */\n\n")
            
            for key in sorted(self.func_signatures.keys()):
                sig = self.func_signatures[key]
                f.write(f"#ifndef GLOBAL_DEF_{key}\n")
                f.write(f"  #undef {sig.name}\n")
                f.write(f"  #define {sig.name} EH_{key}\n")
                f.write(f"  extern {sig.return_type} EH_{key}({sig.parameters});\n")
                f.write(f"#endif\n")
            
            f.write(f"\n/* {len(self.func_signatures)} functions harmonized */\n\n")
            
            # Variable declarations
            f.write("/* ========================================\n")
            f.write(" * Harmonized variable declarations\n")
            f.write(" * ======================================== */\n\n")
            
            for key in sorted(self.var_declarations.keys()):
                var_decl = self.var_declarations[key]
                f.write(f"#ifndef GLOBAL_DEF_{key}\n")
                f.write(f"  #undef {var_decl.name}\n")
                f.write(f"  #define {var_decl.name} EH_{key}\n")
                f.write(f"  extern {var_decl.var_type} EH_{key}{var_decl.array_spec};\n")
                f.write(f"#endif\n")
            
            f.write(f"\n/* {len(self.var_declarations)} variables harmonized */\n\n")
            
            # End C++ compatibility
            f.write("#ifdef __cplusplus\n")
            f.write("}\n")
            f.write("#endif\n\n")
            
            # End header guard
            f.write("#endif /* HARMONIZED_GLOBALS_H */\n")
        
        print(f"      Generated header with {len(types_to_declare)} type declarations")

    def patch_cmake(self):
        """Update CMakeLists.txt with harmonizer configuration."""
        print("  [>] Pass 4: Patching CMake Configuration...")
        
        if not os.path.exists(self.cmake_file):
            print("      Warning: CMakeLists.txt not found")
            return
        
        with open(self.cmake_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove any previous harmonizer injection
        content = re.sub(
            r'# --- Harmonizer.*?# -{20,}',
            '',
            content,
            flags=re.DOTALL
        )
        
        injection = (
            "\n# --- Harmonizer v49.0 Event-Horizon (FINAL) ---\n"
            "# Compiler flags for harmonized source compatibility\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -O3 -fPIC -fno-common -fvisibility=hidden -flto=thin\")\n"
            "\n"
            "# Platform definitions\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C)\n"
            "\n"
            "# Include all harmonized C sources\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# -----------------------------------------------\n"
        )
        
        with open(self.cmake_file, 'w', encoding='utf-8') as f:
            f.write(content + injection)

    def run(self):
        """Execute all harmonization passes in order"""
        print("\n" + "="*60)
        print("Banjo-Kazooie Source Harmonizer v49.0 FINAL")
        print("="*60)
        
        self.sync_files()
        self.extract_sdk_types()
        self.scan_headers_for_types()
        self.map_linkage()
        self.fix_c99_compatibility()
        self.promote_linkage()
        self.generate_header()
        self.patch_cmake()
        
        print("\n" + "="*60)
        print("✓ v49.0 Event-Horizon: FINAL Harmonization Complete")
        print("="*60)
        print(f"  SDK Types Protected: {len(self.sdk_defined_types)}")
        print(f"  Custom Types Discovered: {len(self.all_used_types)}")
        print(f"  Functions Promoted: {len(self.func_signatures)}")
        print(f"  Variables Promoted: {len(self.var_declarations)}")
        print("="*60 + "\n")


if __name__ == "__main__":
    harmonizer = SourceHarmonizerV49(
        android_path="Android/app/src/main/cpp",
        decomp_path="decomp-files"
    )
    harmonizer.run()
