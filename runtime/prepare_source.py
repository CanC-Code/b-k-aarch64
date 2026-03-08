#!/usr/bin/env python3
import os
import re
from pathlib import Path

"""
SourceHarmonizer v75.30 — Environment-Aware Auto-Discovery

═══════════════════════════════════════════════════════════════════════════════
LOG 54 — v75.29 returned 0 results due to path hardcoding.
═══════════════════════════════════════════════════════════════════════════════

KEY UPGRADES in v75.30:
  1. Root Auto-Discovery: Dynamically locates the 'src' and 'include' folders
     regardless of whether it's running on a local PC or GitHub Runner.
  2. Robust Regex: Updated to catch K&R style function definitions often
     found in older N64 decompilation projects.
"""

class SourceHarmonizerV7530:
    def __init__(self):
        # AUTO-DISCOVERY: Search upwards/downwards for the 'src' directory
        self.root = Path(os.getcwd())
        self.target_dir = self.find_project_root()
        self.function_map = {} 
        self.stats = {"signatures_mapped": 0, "prototypes_fixed": 0, "files_scanned": 0}

    def find_project_root(self):
        """Finds the directory containing 'src' and 'include'."""
        possible_paths = [
            self.root,
            self.root / "Android/app/src/main/cpp",
            self.root / "decomp",
            self.root / ".." 
        ]
        for p in possible_paths:
            if (p / "src").exists():
                print(f"[!] Project Root Discovered: {p}")
                return p
        print("[!] ERROR: Could not locate 'src' directory!")
        return self.root

    def map_all_functions(self):
        print("[>] Indexing project signatures...")
        # Enhanced Regex to catch: ReturnType Name(Params) {
        # Handles multi-line return types and spacing
        def_pat = re.compile(r'^([\w\s\*]+?)\b(func_[A-Z0-9_]+)\s*\(([^)]*)\)\s*\{', re.MULTILINE)
        
        for file_path in self.target_dir.rglob('*.c'):
            self.stats["files_scanned"] += 1
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            for match in def_pat.finditer(content):
                ret_type, name, params = match.groups()
                # Clean up whitespace/newlines in return types
                ret_type = " ".join(ret_type.split())
                self.function_map[name] = {"ret": ret_type, "params": params.strip()}
                self.stats["signatures_mapped"] += 1

    def sync_prototypes(self):
        print(f"[>] Synchronizing {len(self.function_map)} signatures across files...")
        for file_path in self.target_dir.rglob('*.c'):
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            original = content
            
            # Update the Auto-Prototype blocks created in v75.27/28
            proto_match = re.search(r'// --- SH (?:Auto|Precise)-Prototypes ---\n(.*?)\n// -+', content, re.DOTALL)
            if proto_match:
                lines = proto_match.group(1).split('\n')
                new_lines = []
                for line in lines:
                    name_match = re.search(r'extern (?:void\*|[\w\*]+) (func_[A-Z0-9_]+)', line)
                    if name_match:
                        name = name_match.group(1)
                        if name in self.function_map:
                            sig = self.function_map[name]
                            new_lines.append(f"extern {sig['ret']} {name}({sig['params']});")
                            self.stats["prototypes_fixed"] += 1
                            continue
                    new_lines.append(line)
                
                new_block = f"// --- SH Precise-Prototypes ---\n" + "\n".join(new_lines) + "\n// ----------------------------"
                content = content.replace(proto_match.group(0), new_block)

            if content != original:
                file_path.write_text(content, encoding='utf-8')

    def run(self):
        self.map_all_functions()
        if self.stats["signatures_mapped"] > 0:
            self.sync_prototypes()
        
        print(f"\n[+] v75.30 Auto-Discovery Complete.")
        print(f"    - Files Scanned: {self.stats['files_scanned']}")
        print(f"    - Signatures Mapped: {self.stats['signatures_mapped']}")
        print(f"    - Prototypes Reified: {self.stats['prototypes_fixed']}")

if __name__ == "__main__":
    SourceHarmonizerV7530().run()
