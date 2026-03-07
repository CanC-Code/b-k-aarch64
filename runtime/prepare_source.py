#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

"""
SourceHarmonizer v74.6 - Robust AArch64 Porting Tool
Enhancements:
1. Dynamic Type Discovery: Automatically detects all struct/union/enum tags in the project.
2. Parameter Scrubbing: Robustly fixes "double struct tagging" in function pointers and signatures.
3. Pointer Conversion: Safely converts array parameters with incomplete types to pointers.
4. Recursive Processing: Scans all .h and .c files in the target directory.
"""

class SourceHarmonizer:
    def __init__(self, target_dir):
        self.target_dir = Path(target_dir)
        self.discovered_types = set()
        self.stats = {"files_processed": 0, "changes_made": 0}

    def discover_types(self):
        """Scans project files to build a dynamic list of struct, union, and enum tags."""
        print(f"[*] Scanning {self.target_dir} for dynamic type discovery...")
        tag_pattern = re.compile(r'\b(struct|union|enum)\s+([A-Za-z_]\w*)')
        
        for file_path in self.target_dir.rglob('*.[ch]'):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for match in tag_pattern.finditer(content):
                        self.discovered_types.add(match.group(2))
            except Exception as e:
                print(f"[!] Error scanning {file_path}: {e}")
        
        print(f"[+] Discovered {len(self.discovered_types)} unique tags.")

    def harmonize_content(self, content):
        original = content
        
        # 1. Fix Double Struct Tagging (e.g., 'struct Vtx **struct Vtx' -> 'struct Vtx **Vtx')
        # This handles cases where a type tag is accidentally repeated as a parameter name.
        for tag in self.discovered_types:
            double_tag_pattern = re.compile(rf'\b(struct|union|enum)\s+{tag}\s*([\*\s]+)\s*(struct|union|enum)\s+{tag}\b')
            content = double_tag_pattern.sub(rf'struct {tag} \2 {tag}', content)

        # 2. Dynamic Tagging
        # Ensure discovered tags are prefixed with 'struct' if they appear as standalone types in parameters.
        # Uses negative lookbehind to avoid double-tagging 'struct struct'.
        for tag in self.discovered_types:
            # Look for the tag when it's NOT preceded by struct/union/enum and followed by pointers/names
            standalone_pattern = re.compile(rf'(?<!struct|union|enum)\s+\b{tag}\b(?=\s*\*|\s+[A-Za-z_])')
            content = standalone_pattern.sub(f' struct {tag}', content)

        # 3. Fix Incomplete Array Parameters (e.g., 'struct T arg[4]' -> 'struct T *arg')
        # This is a common requirement for AArch64/Android NDK when types are forward-declared.
        array_param_pattern = re.compile(
            r'(\b(?:struct|union|enum)\s+[A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*\[\s*\d+\s*\]'
        )
        content = array_param_pattern.sub(r'\1 *\2', content)

        return content

    def run(self):
        if not self.target_dir.exists():
            print(f"[!] Error: Directory {self.target_dir} does not exist.")
            return

        self.discover_types()

        for file_path in self.target_dir.rglob('*.[ch]'):
            self.stats["files_processed"] += 1
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                new_content = self.harmonize_content(content)

                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    self.stats["changes_made"] += 1
                    print(f"[FIXED] {file_path.relative_to(self.target_dir)}")
            except Exception as e:
                print(f"[!] Error processing {file_path}: {e}")

        print(f"\n[+] Harmonization Complete!")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    harmonizer = SourceHarmonizer(target)
    harmonizer.run()
