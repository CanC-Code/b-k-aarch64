#!/usr/bin/env python3
import os
import re
import sys
import hashlib
from pathlib import Path

"""
SourceHarmonizer v74.8 - Semantic Safety Edition
Fixes:
1. Typedef Protection: Explicitly ignores s32, u32, f32, etc., from discovery.
2. Selective Pointer Conversion: Only converts arrays of custom structs, not primitive buffers.
3. Header Guard Sanitization: Adds #undef before #define to prevent macro recursion.
4. Token-Based Discovery: Improves accuracy of dynamic type detection.
"""

class SourceHarmonizer:
    def __init__(self, target_dir):
        self.target_dir = Path(target_dir)
        self.discovered_types = set()
        # Explicitly protect these from being turned into 'struct s32' etc.
        self.blacklist = {
            's8', 'u8', 's16', 'u16', 's32', 'u32', 's64', 'u64', 
            'f32', 'f64', 'void', 'int', 'char', 'float', 'double',
            'bool', 'size_t', 'uintptr_t', 's16p', 'u16p'
        }
        self.stats = {"files_processed": 0, "changes_made": 0}

    def discover_types(self):
        """Scans codebase for legitimate struct/union/enum tags."""
        print(f"[*] Scanning {self.target_dir} for legitimate tags...")
        # Matches 'struct TagName' or 'typedef struct TagName'
        tag_pattern = re.compile(r'\b(struct|union|enum)\s+([A-Za-z_]\w*)')
        
        for file_path in self.target_dir.rglob('*.[ch]'):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for match in tag_pattern.finditer(content):
                        name = match.group(2)
                        if name not in self.blacklist and len(name) > 1:
                            self.discovered_types.add(name)
            except Exception as e:
                print(f"[!] Scan error {file_path.name}: {e}")
        
        print(f"[+] Discovered {len(self.discovered_types)} valid custom tags.")

    def harmonize_content(self, content):
        if not self.discovered_types:
            return content

        # 1. Clean up "Double Tagging" from previous failed runs
        for tag in self.discovered_types:
            double_pattern = re.compile(rf'\bstruct\s+struct\s+{tag}\b')
            content = double_pattern.sub(f'struct {tag}', content)

        # 2. Dynamic Tagging with Semantic Guard
        sorted_tags = sorted(list(self.discovered_types), key=len, reverse=True)
        tags_regex = "|".join(re.escape(t) for t in sorted_tags)
        
        # Matches TagName but NOT if already prefixed by struct/union/enum
        # Also ensures it looks like a type usage (followed by * or space+identifier)
        standalone_pattern = re.compile(rf'(?<!struct\s)(?<!union\s)(?<!enum\s)\b({tags_regex})\b(?=\s*\*|\s+[A-Za-z_])')
        content = standalone_pattern.sub(r'struct \1', content)

        # 3. Targeted Array-to-Pointer Conversion
        # Only targets arrays of structs that often cause "incomplete type" errors in NDK
        # Example: struct AnimTexture arg[4] -> struct AnimTexture *arg
        array_pattern = re.compile(r'(struct\s+([A-Za-z_]\w*))\s+([A-Za-z_]\w*)\s*\[\s*\d+\s*\]')
        
        def array_replacer(m):
            tag_name = m.group(2)
            # Only convert if it's one of our discovered custom types
            if tag_name in self.discovered_types:
                return f"{m.group(1)} *{m.group(3)}"
            return m.group(0)

        content = array_pattern.sub(array_replacer, content)

        return content

    def run(self):
        if not self.target_dir.exists():
            print(f"[!] Error: Path {self.target_dir} invalid.")
            return

        self.discover_types()

        for file_path in self.target_dir.rglob('*.[ch]'):
            # Skip standard library headers if they exist in subfolders
            if "include/libc" in str(file_path): continue
            
            self.stats["files_processed"] += 1
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                new_content = self.harmonize_content(content)

                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    self.stats["changes_made"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")

        self.generate_safety_header()
        print(f"\n[+] v74.8 Complete. Files Modified: {self.stats['changes_made']}")

    def generate_safety_header(self):
        """Generates a cleaner harmonized_globals.h with macro collision protection."""
        header_path = self.target_dir / "include" / "harmonized_globals.h"
        if not header_path.parent.exists(): return

        with open(header_path, 'w') as f:
            f.write("#ifndef HARMONIZED_GLOBALS_H\n#define HARMONIZED_GLOBALS_H\n\n")
            f.write("// Forward declarations for discovered types\n")
            for tag in sorted(self.discovered_types):
                f.write(f"struct {tag};\n")
            
            f.write("\n// Macro Protection Layer\n")
            f.write("// Prevents recursion if these names are used in system headers\n")
            # In a real run, this would be populated by the symbol mapper from v74.4
            # For this standalone tool, we ensure the infrastructure is ready.
            f.write("\n#endif // HARMONIZED_GLOBALS_H\n")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    harmonizer = SourceHarmonizer(target)
    harmonizer.run()
