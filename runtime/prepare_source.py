import re
import os
import hashlib

# SourceHarmonizer v74.5 - AArch64 Android Porting Tool
# Fixes: Incomplete array types and double-struct tagging in parameters.

class SourceHarmonizer:
    def __init__(self):
        self.version = "74.5"
        # Whitelist of custom types that need 'struct' or 'union' prefixes
        self.struct_types = {
            'Vtx', 'Gfx', 'Mtx', 'Vp', 'LookAt', 'Hilite', 'Lightsn', 'Lightt',
            'Ambient', 'Light', 'PosColor', 'u64', 's64', 'f32', 'f64',
            'AnimTexture', 'Cube', 'Pyramid', 'Actor', 'Entity', 'Sprite'
        }
        self.conversion_map = {}

    def tag_types(self, signature):
        """Prefixes custom types with 'struct' only if they are in type positions."""
        for t in self.struct_types:
            # Context-aware regex:
            # 1. Match the type 't'
            # 2. Ensure it's NOT already preceded by 'struct ', 'union ', or 'enum '
            # 3. Lookahead: Must be followed by pointers (**) OR whitespace and a word/char
            #    AND NOT followed by a comma or closing paren (which indicates a variable name).
            pattern = rf'(?<!struct\s)(?<!union\s)(?<!enum\s)\b({t})\b(?=\s*\*|\s+\w)(?![ \t]*[,)])'
            signature = re.sub(pattern, r'struct \1', signature)
        
        # Cleanup any accidental double-tagging that slipped through
        signature = signature.replace('struct struct', 'struct')
        return signature

    def fix_array_parameters(self, signature):
        """Converts 'struct Type name[N]' to 'struct Type *name' to avoid incomplete type errors."""
        # Matches: struct Type name[Number]
        array_pattern = r'(struct\s+\w+)\s+(\w+)\[\d+\]'
        return re.sub(array_pattern, r'\1 *\2', signature)

    def harmonize_function(self, line):
        if not line.strip().startswith('extern'):
            return line
            
        # 1. Apply struct tagging with context awareness
        line = self.tag_types(line)
        
        # 2. Fix incomplete array types in parameters
        line = self.fix_array_parameters(line)
        
        # 3. Handle specific double-prefix edge cases (e.g., struct Vtx **struct Vtx)
        # Identify 'struct Type **struct Name' and fix to 'struct Type **Name'
        double_trouble = r'(struct\s+\w+\s+\*\*+)struct\s+(\w+)'
        line = re.sub(double_trouble, r'\1\2', line)
        
        return line

    def process_file(self, filepath):
        with open(filepath, 'r') as f:
            lines = f.readlines()
            
        new_lines = []
        for line in lines:
            if "extern void BKA_F_" in line or "extern " in line:
                new_lines.append(self.harmonize_function(line))
            else:
                new_lines.append(line)
                
        with open(filepath, 'w') as f:
            f.writelines(new_lines)

# Execution logic for harmonized_globals.h
if __name__ == "__main__":
    harmonizer = SourceHarmonizer()
    target_h = "Android/app/src/main/cpp/include/harmonized_globals.h"
    if os.path.exists(target_h):
        print(f"Harmonizing {target_h} v{harmonizer.version}...")
        harmonizer.process_file(target_h)
        print("Success: Fixed array types and parameter naming collisions.")
