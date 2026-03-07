#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

"""
SourceHarmonizer v74.7 - Robust AArch64 Porting Tool
Fixes:
1. Fixed-Width Lookbehind Error: Replaced variable-width lookbehind with a capture group and replacement logic.
2. Single-Pass Performance: Optimized type tagging to use a single large regex for all discovered tags.
3. Enhanced Parameter Scrubbing: Prevents corruption of function signatures.
"""

class SourceHarmonizer:
    def __init__(self, target_dir):
        self.target_dir = Path(target_dir)
        self.discovered_types = set()
        self.stats = {"files_processed": 0, "changes_made": 0}

    def discover_types(self):
        """Scans project files to build a dynamic list of struct, union, and enum tags."""
        print(f"[*] Scanning {self.target_dir} for dynamic type discovery...")
        # Capture tags defined in the codebase
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
        if not self.discovered_types:
            return content

        # 1. Fix Double Struct Tagging (e.g., 'struct Vtx **struct Vtx' -> 'struct Vtx **Vtx')
        for tag in self.discovered_types:
            double_tag_pattern = re.compile(rf'\b(struct|union|enum)\s+{tag}\s*([\*\s]+)\s*(struct|union|enum)\s+{tag}\b')
            content = double_tag_pattern.sub(rf'struct {tag} \2 {tag}', content)

        # 2. Dynamic Tagging (The Fixed Logic)
        # Create one large regex for all tags to improve performance
        # Sort by length descending to match longer tags first (e.g., 'Vtx_t' before 'Vtx')
        sorted_tags = sorted(list(self.discovered_types), key=len, reverse=True)
        tags_regex = "|".join(re.escape(t) for t in sorted_tags)
        
        # Pattern: (Optional Prefix) + (The Tag) + (Pointer/Space suffix)
        # Group 1: Optional struct/union/enum
        # Group 2: The actual type name
        # Group 3: Following spaces or asterisks
        standalone_pattern = re.compile(rf'(\b(?:struct|union|enum)\s+)?\b({tags_regex})\b([\s\*]+[A-Za-z_]?)')

        def tag_replacer(match):
            prefix = match.group(1)
            tag_name = match.group(2)
            suffix = match.group(3)
            
            # If it already has a prefix, return it as is
            if prefix:
                return match.group(0)
            
            # Otherwise, add the 'struct' prefix
            # Note: BK project uses 'struct' for almost all missing tags
            return f"struct {tag_name}{suffix}"

        content = standalone_pattern.sub(tag_replacer, content)

        # 3. Fix Incomplete Array Parameters (e.g., 'struct T arg[4]' -> 'struct T *arg')
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
                # Use 'ignore' for encoding to handle non-UTF8 characters in comments/assets
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                new_content = self.harmonize_content(content)

                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    self.stats["changes_made"] += 1
                    # print(f"[FIXED] {file_path}") # Optional: uncomment for verbose logs
            except Exception as e:
                print(f"[!] Error processing {file_path}: {e}")

        print(f"\n[+] Harmonization Complete!")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")

if __name__ == "__main__":
    # Default to current directory if no path provided
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    harmonizer = SourceHarmonizer(target)
    harmonizer.run()
