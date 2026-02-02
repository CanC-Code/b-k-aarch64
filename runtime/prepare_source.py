#!/usr/bin/env python3
"""
Banjo-Kazooie Decompilation Android Harmonizer v48.0
Dynamically patches N64 source files for Android compatibility.
Aligns C semantics with modern compilation requirements.
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
    is_bss: bool  # True if uninitialized (ends with ;)


class SourceHarmonizerV48:
    """
    Harmonizes N64 decompiled source files for Android compilation.
    
    Key responsibilities:
    1. Prevent typedef redefinition conflicts with SDK headers
    2. Correctly parse and extract type information from C declarations
    3. Promote static symbols to global scope with unique names
    4. Generate conflict-free header with forward declarations
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
        self.discovered_types: Set[str] = set()
        self.sdk_defined_types: Set[str] = set()
        
        # Reserved SDK types that MUST NOT be redefined
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
            
            # N64 Audio Library types (libaudio.h)
            'ALHeap', 'ALLink', 'ALGlobals',
            'ALVoice', 'ALVoiceConfig', 
            'ALSound', 'ALSoundState',
            'ALBank', 'ALBankFile', 'ALInstrument', 'ALInstrumentListItem',
            'ALKeyMap', 'ALWave', 'ALEnvelope', 'ALADPCMBook', 'ALRawLoop',
            'ALADPCMLoop', 'ALMIDIvoice',
            'ALSeq', 'ALSeqData', 'ALSeqFile', 'ALSeqMarker', 
            'ALSeqPlayer', 'ALSeqpConfig', 'ALCSPlayer',
            'ALCSeq', 'ALCSeqPlayer',  # CRITICAL: Already typedef'd in SDK
            'ALSndPlayer', 'ALSndpConfig', 
            'ALSynth', 'ALSynConfig',  # CRITICAL: Already typedef'd in SDK
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
        
        # Reserved function/variable names that should not be renamed
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
        
        # Clean and recreate target directories
        for folder in [self.src_target, self.include_target]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
            os.makedirs(folder, exist_ok=True)

        # Copy src/ and include/ directories
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
        This prevents us from creating conflicting typedef declarations.
        """
        print("  [>] Pass 0.5: Scanning SDK Headers for Type Conflicts...")
        
        # Patterns to match various typedef forms
        patterns = [
            # typedef struct X { ... } Y;
            re.compile(r'typedef\s+struct\s+\w*\s*\{[^}]*\}\s*(\w+)\s*;', re.DOTALL),
            # typedef struct X Y;
            re.compile(r'typedef\s+struct\s+\w+\s+(\w+)\s*;'),
            # typedef ... Y;
            re.compile(r'typedef\s+[^;]+\s+(\w+)\s*;'),
        ]
        
        # Include directories to scan
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
                            
                        # Extract all typedef'd type names
                        for pattern in patterns:
                            for match in pattern.finditer(content):
                                type_name = match.group(1)
                                if type_name and type_name[0].isupper():  # Likely a type
                                    self.sdk_defined_types.add(type_name)
                                    
                    except Exception as e:
                        print(f"      Warning: Could not scan {filename}: {e}")
        
        print(f"      Found {len(self.sdk_defined_types)} SDK-defined types")

    def parse_c_type(self, type_str: str) -> List[str]:
        """
        Extract type names from a C type declaration string.
        
        Examples:
            'SnackerCtlState' -> ['SnackerCtlState']
            'const AnimSprite*' -> ['AnimSprite']
            'struct NodeProp*' -> ['NodeProp']
            'void' -> []
            
        Returns only CamelCase type names (custom types), not primitives.
        """
        # Remove common keywords and qualifiers
        type_str = re.sub(r'\b(const|static|extern|inline|volatile|restrict)\b', '', type_str)
        type_str = re.sub(r'\b(struct|union|enum)\b', '', type_str)
        
        # Remove pointer/array notation
        type_str = re.sub(r'[\*\[\]]+', ' ', type_str)
        
        # Extract CamelCase identifiers (starts with capital letter)
        # This is the pattern for custom types in the Banjo codebase
        types = re.findall(r'\b([A-Z][a-zA-Z0-9_]*)\b', type_str)
        
        # Filter out reserved types
        valid_types = []
        for t in types:
            if (t not in self.reserved_types and 
                t not in self.sdk_defined_types):
                valid_types.append(t)
        
        return valid_types

    def extract_return_type(self, signature: str) -> str:
        """
        Extract return type from a function signature string.
        
        Input: 'SnackerCtlState funcname(void)'
        Output: 'SnackerCtlState'
        
        Handles complex cases like:
        - 'static void* func(int x)'
        - 'const struct NodeProp* func(void)'
        """
        # Remove function name and parameters
        # Match everything before the function name (last word before '(')
        match = re.match(r'^(.*?)\s+([a-zA-Z_]\w*)\s*\(', signature)
        if match:
            return match.group(1).strip()
        return 'void'

    def map_linkage(self):
        """
        Parse all C source files to extract:
        - Static function signatures
        - Static variable declarations  
        - Type information from all declarations
        """
        print("  [>] Pass 1: Semantic Type Mapping...")
        
        # Pattern for static function declarations
        # Matches: static <return_type> <name>(<params>) {
        # Must not be inline or extern
        func_pattern = re.compile(
            r'^static\s+'                           # static keyword
            r'(?!.*\binline\b)(?!.*\bextern\b)'    # negative lookahead for inline/extern
            r'((?:const\s+)?'                       # optional const
            r'(?:struct\s+|union\s+|enum\s+)?'     # optional struct/union/enum
            r'[\w\s\*]+?)\s+'                       # return type
            r'([a-zA-Z_]\w*)\s*'                    # function name
            r'\(([^\)]*)\)\s*'                      # parameters
            r'\{',                                   # opening brace
            re.MULTILINE
        )
        
        # Pattern for static variable declarations
        # Matches: static [const] <type> <name>[array] [=|:|;]
        var_pattern = re.compile(
            r'^static\s+'
            r'(const\s+)?'                          # optional const
            r'((?:struct\s+|union\s+)?[\w\s\*]+)\s+'  # type
            r'([a-zA-Z_]\w*)'                        # variable name
            r'(\s*\[[^\]]*\])*\s*'                  # optional array spec
            r'([=:;])',                              # initializer or terminator
            re.MULTILINE
        )
        
        # Pattern to find struct/typedef definitions
        struct_pattern = re.compile(
            r'(?:typedef\s+)?'
            r'(?:struct|union)\s+'
            r'(\w+)\s*'
            r'(?:\{|;)',
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
                    
                    # Extract struct definitions for type discovery
                    for match in struct_pattern.finditer(content):
                        struct_name = match.group(1)
                        if struct_name and struct_name[0].isupper():
                            discovered_types = self.parse_c_type(struct_name)
                            self.discovered_types.update(discovered_types)
                    
                    # Extract function signatures
                    for match in func_pattern.finditer(content):
                        return_type_raw = match.group(1).strip()
                        func_name = match.group(2).strip()
                        params_raw = match.group(3).strip() or "void"
                        
                        # Skip reserved functions
                        if func_name in self.reserved_names:
                            continue
                        
                        # Store function signature
                        key = f"{file_id}_{func_name}"
                        self.func_signatures[key] = FunctionSignature(
                            name=func_name,
                            return_type=return_type_raw,
                            parameters=params_raw
                        )
                        
                        # Extract types from return type and parameters
                        full_signature = f"{return_type_raw} {params_raw}"
                        discovered_types = self.parse_c_type(full_signature)
                        self.discovered_types.update(discovered_types)
                    
                    # Extract variable declarations
                    for match in var_pattern.finditer(content):
                        is_const = match.group(1) is not None
                        var_type = match.group(2).strip()
                        var_name = match.group(3).strip()
                        array_spec = match.group(4).strip() if match.group(4) else ""
                        terminator = match.group(5)
                        
                        # Build full type string
                        full_type = ("const " if is_const else "") + var_type
                        
                        # Store variable declaration
                        key = f"{file_id}_{var_name}"
                        self.var_declarations[key] = VariableDeclaration(
                            name=var_name,
                            var_type=full_type,
                            array_spec=array_spec,
                            is_bss=(terminator == ';')
                        )
                        
                        # Extract types from variable type
                        discovered_types = self.parse_c_type(full_type)
                        self.discovered_types.update(discovered_types)
                        
                except Exception as e:
                    print(f"      Warning: Error processing {filename}: {e}")
        
        print(f"      Processed {file_count} C files")
        print(f"      Discovered {len(self.discovered_types)} custom types")
        print(f"      Found {len(self.func_signatures)} static functions")
        print(f"      Found {len(self.var_declarations)} static variables")

    def promote_linkage(self):
        """
        Transform static functions and variables to have global visibility.
        
        Changes:
        - static void func(...) { -> __attribute__(...) void EH_<id>_func(...) {
        - static int var; -> __attribute__(...) int EH_<id>_var;
        
        Adds macro guards to prevent duplicate definition errors.
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
                            # Uninitialized variable: static type var;
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
                            # Initialized variable: static type var = ...
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
                            # CRITICAL: Include ultra64.h FIRST to define SDK types
                            # Then include our harmonized header
                            f.write('#include <ultra64.h>\n')
                            f.write('#include "harmonized_globals.h"\n')
                            f.write(content)
                        modified_count += 1
                        
                except Exception as e:
                    print(f"      Warning: Error promoting linkage in {filename}: {e}")
        
        print(f"      Modified {modified_count} source files")

    def generate_header(self):
        """
        Generate harmonized_globals.h with forward declarations and macros.
        
        Only declares types that are NOT already in SDK headers.
        Uses include guards to prevent duplicate definitions.
        """
        print("  [>] Pass 3: Generating Macro-Shielded Header...")
        
        header_path = os.path.join(self.include_target, "harmonized_globals.h")
        
        with open(header_path, 'w', encoding='utf-8') as f:
            # Header guard
            f.write("#ifndef HARMONIZED_GLOBALS_H\n")
            f.write("#define HARMONIZED_GLOBALS_H\n\n")
            
            # Standard includes
            f.write("/* Standard library headers */\n")
            f.write("#include <stdbool.h>\n")
            f.write("#include <stdint.h>\n")
            f.write("#include <stddef.h>\n\n")
            
            # C++ compatibility
            f.write("#ifdef __cplusplus\n")
            f.write("extern \"C\" {\n")
            f.write("#endif\n\n")
            
            # Forward declare custom types (but NOT SDK types)
            f.write("/* Forward declarations for custom types */\n")
            f.write("/* SDK types (from ultra64.h, libaudio.h) are NOT redeclared */\n\n")
            
            types_declared = 0
            for type_name in sorted(self.discovered_types):
                # Skip if type is in SDK or reserved
                if type_name in self.sdk_defined_types:
                    continue
                if type_name in self.reserved_types:
                    continue
                    
                # Use unique guard for each type
                f.write(f"#ifndef TYPE_DEFINED_{type_name}\n")
                f.write(f"  typedef struct {type_name} {type_name};\n")
                f.write(f"  #define TYPE_DEFINED_{type_name}\n")
                f.write(f"#endif\n")
                types_declared += 1
            
            f.write(f"\n/* {types_declared} custom types declared */\n\n")
            
            # Function declarations
            f.write("/* Harmonized function declarations */\n")
            for key in sorted(self.func_signatures.keys()):
                sig = self.func_signatures[key]
                f.write(f"#ifndef GLOBAL_DEF_{key}\n")
                f.write(f"  #undef {sig.name}\n")
                f.write(f"  #define {sig.name} EH_{key}\n")
                f.write(f"  extern {sig.return_type} EH_{key}({sig.parameters});\n")
                f.write(f"#endif\n")
            
            f.write(f"\n/* {len(self.func_signatures)} functions harmonized */\n\n")
            
            # Variable declarations
            f.write("/* Harmonized variable declarations */\n")
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
        
        print(f"      Generated header with {types_declared} type declarations")

    def patch_cmake(self):
        """
        Update CMakeLists.txt with harmonizer configuration.
        Adds necessary compiler flags and source file glob.
        """
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
        
        # Add new harmonizer configuration
        injection = (
            "\n# --- Harmonizer v48.0 Event-Horizon (Production) ---\n"
            "# Compiler flags for harmonized source compatibility\n"
            "set(CMAKE_C_FLAGS \"${CMAKE_C_FLAGS} -O3 -fPIC -fno-common -fvisibility=hidden -flto=thin\")\n"
            "\n"
            "# Platform definitions\n"
            "add_definitions(-D__arm64__ -D_LANGUAGE_C)\n"
            "\n"
            "# Include all harmonized C sources\n"
            "file(GLOB_RECURSE ALL_C \"src/*.c\")\n"
            "target_sources(bkawrapper PRIVATE ${ALL_C})\n"
            "# ----------------------------------------------------\n"
        )
        
        with open(self.cmake_file, 'w', encoding='utf-8') as f:
            f.write(content + injection)

    def run(self):
        """Execute all harmonization passes in order"""
        print("\n" + "="*60)
        print("Banjo-Kazooie Source Harmonizer v48.0")
        print("="*60)
        
        self.sync_files()
        self.extract_sdk_types()
        self.map_linkage()
        self.promote_linkage()
        self.generate_header()
        self.patch_cmake()
        
        print("\n" + "="*60)
        print("✓ v48.0 Event-Horizon: Harmonization Complete")
        print("="*60)
        print(f"  SDK Types Protected: {len(self.sdk_defined_types)}")
        print(f"  Custom Types Found: {len(self.discovered_types)}")
        print(f"  Functions Promoted: {len(self.func_signatures)}")
        print(f"  Variables Promoted: {len(self.var_declarations)}")
        print("="*60 + "\n")


if __name__ == "__main__":
    harmonizer = SourceHarmonizerV48(
        android_path="Android/app/src/main/cpp",
        decomp_path="decomp-files"
    )
    harmonizer.run()
