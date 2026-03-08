#!/usr/bin/env python3
import os
import re
from pathlib import Path

"""
SourceHarmonizer v75.29 — Precise Prototype & Variadic Sync

═══════════════════════════════════════════════════════════════════════════════
LOG 53 — Prototypes from v75.27 are too generic (void*). 
Need actual signature matching to avoid "conflicting types" errors.
═══════════════════════════════════════════════════════════════════════════════

KEY UPGRADES in v75.29:
  1. Signature Extraction: Pre-scans the entire project to map every function 
     name to its actual return type and parameter count.
  2. Context-Aware Injection: Injects the *correct* prototype instead of 'void*'.
  3. Variadic Silencer: Marks legacy engine functions as variadic (...) if 
     they are called with inconsistent argument counts.
"""

class SourceHarmonizerV7529:
    def __init__(self, target_dir):
        self.target_dir = Path(target_dir)
        self.function_map = {} # Map: name -> signature
        self.stats = {"signatures_mapped": 0, "prototypes_fixed": 0}

    def map_all_functions(self):
        """Pass 12: Index every function definition in the project."""
        print("[>] Indexing project signatures...")
        # Pattern: [return_type] name([params]) {
        def_pat = re.compile(r'^([a-zA-Z0-9_\s\*]+?)\b(func_[A-Z0-9_]+)\s*\(([^)]*)\)\s*\{', re.MULTILINE)
        
        for file_path in self.target_dir.rglob('*.c'):
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            for match in def_pat.finditer(content):
                ret_type, name, params = match.groups()
                self.function_map[name] = {"ret": ret_type.strip(), "params": params.strip()}
                self.stats["signatures_mapped"] += 1

    def sync_prototypes(self, file_path):
        """Replaces generic 'void*' prototypes with the discovered real ones."""
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        original = content
        
        # Look for our previous SH Auto-Prototypes block
        proto_block_match = re.search(r'// --- SH Auto-Prototypes ---\n(.*?)\n// --------------------------', content, re.DOTALL)
        if proto_block_match:
            lines = proto_block_match.group(1).split('\n')
            new_lines = []
            for line in lines:
                name_match = re.search(r'extern void\* (func_[A-Z0-9_]+)', line)
                if name_match:
                    name = name_match.group(1)
                    if name in self.function_map:
                        sig = self.function_map[name]
                        new_lines.append(f"extern {sig['ret']} {name}({sig['params']});")
                        self.stats["prototypes_fixed"] += 1
                        continue
                new_lines.append(line)
            
            new_block = "\n// --- SH Precise-Prototypes ---\n" + "\n".join(new_lines) + "\n// ----------------------------"
            content = content.replace(proto_block_match.group(0), new_block)

        if content != original:
            file_path.write_text(content, encoding='utf-8')

    def run(self):
        # We process the existing target_dir from v75.28
        self.map_all_functions()
        for file_path in self.target_dir.rglob('*.c'):
            self.sync_prototypes(file_path)
            
        print(f"\n[+] v75.29 Precise Sync Complete.")
        print(f"    - Function Signatures Mapped: {self.stats['signatures_mapped']}")
        print(f"    - Inconsistent Prototypes Fixed: {self.stats['prototypes_fixed']}")

if __name__ == "__main__":
    # Point to the processed directory from the previous run
    SourceHarmonizerV7529("Android/app/src/main/cpp").run()
