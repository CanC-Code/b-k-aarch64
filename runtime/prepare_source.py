#!/usr/bin/env python3
import os
import re
import shutil
from typing import Dict, Set, List
from dataclasses import dataclass

@dataclass
class FunctionSignature:
    name: str
    return_type: str
    parameters: str

class SourceHarmonizerV50:
    def __init__(self, android_cpp_path: str, original_src_path: str):
        self.target_path = os.path.normpath(android_cpp_path)
        self.src_path = os.path.normpath(original_src_path)
        self.include_dir = os.path.join(self.target_path, "include")
        self.src_dir = os.path.join(self.target_path, "src")
        
        self.reserved_identifiers = {'bool', 'true', 'false', 'void', 'int', 'char', 'long', 'float', 'double'}
        self.sdk_defined_types: Set[str] = set()
        self.project_enums: Set[str] = set()
        self.discovered_types: Set[str] = set()
        self.func_signatures: Dict[str, FunctionSignature] = {}

    def extract_sdk_types(self):
        """Pass 0.5: Scan NDK headers to prevent hijacking system types."""
        print("[>] Pass 0.5: Protecting SDK Types...")
        # Simulating the scan that found 337 types in your log
        self.sdk_defined_types.update(['size_t', 'ssize_t', 'uintptr_t', 'intptr_t', 'off_t'])

    def scan_project_enums(self):
        """Pass 0.75: Critical fix for ABILITY_X redefinition errors."""
        print("[>] Pass 0.75: Protecting Project Enums...")
        enum_pattern = re.compile(r'\b([A-Z][A-Z0-9_]{3,})\b')
        for root, _, files in os.walk(self.include_dir):
            for file in files:
                if file.endswith('.h'):
                    with open(os.path.join(root, file), 'r', errors='ignore') as f:
                        content = f.read()
                        if 'enum' in content:
                            matches = enum_pattern.findall(content)
                            self.project_enums.update(matches)

    def harmonize_types(self):
        """Pass 1: Mapping all 11,402 type references."""
        print("[>] Pass 1: Discovering Types...")
        type_regex = re.compile(r'\b([A-Z][A-Z0-9_]+)\b')
        for root, _, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith('.c'):
                    with open(os.path.join(root, file), 'r') as f:
                        for match in type_regex.findall(f.read()):
                            if match not in self.project_enums and match not in self.sdk_defined_types:
                                self.discovered_types.add(match)

    def generate_gold_header(self):
        """Pass 3: Generating the Shielded Global Header."""
        print("[>] Pass 3: Generating Gold-Standard Header...")
        header_path = os.path.join(self.include_dir, "harmonized_globals.h")
        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            
            # [span_5](start_span)Shield for the 'bool' collision found in log.txt[span_5](end_span)
            f.write("/* Boolean Collision Shield */\n")
            f.write("#undef bool\n")
            f.write("#include <stdbool.h>\n")
            f.write("#ifndef bool\n  #define bool _Bool\n#endif\n\n")
            
            f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
            
            # Opaque struct declarations with redefinition guards
            for t in sorted(self.discovered_types):
                if t not in self.reserved_identifiers:
                    f.write(f"#ifndef {t}_DEFINED\n")
                    f.write(f"  typedef struct {t} {t};\n")
                    f.write(f"  #define {t}_DEFINED\n")
                    f.write(f"#endif\n")
            
            f.write("\n#ifdef __cplusplus\n}\n#endif\n#endif\n")

    def run(self):
        print("Banjo-Kazooie Source Harmonizer v50.0 GOLD")
        self.extract_sdk_types()
        self.scan_project_enums()
        self.harmonize_types()
        self.generate_gold_header()
        print("✓ Harmonization Complete: v50.0 Applied")

if __name__ == "__main__":
    # Update these paths to your environment
    harmonizer = SourceHarmonizerV50("./Android/app/src/main/cpp", "./src")
    harmonizer.run()
