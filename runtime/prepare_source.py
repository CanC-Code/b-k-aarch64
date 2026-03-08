#!/usr/bin/env python3
import os
import re
import subprocess
from pathlib import Path

"""
SourceHarmonizer v75.40 — Deep Checkout Verification
═══════════════════════════════════════════════════════════════════════════════
LOG 67 — Added a 'git submodule update' fallback to handle shallow CI clones.
═══════════════════════════════════════════════════════════════════════════════
"""

class SourceHarmonizerV7540:
    def __init__(self):
        self.root = Path(os.getcwd()).resolve()
        self.src_path = os.path.join(str(self.root), "decomp-files", "src")
        self.function_map = {} 

    def ensure_submodules(self):
        """Forces a recursive update if the src directory is empty."""
        if not os.path.exists(self.src_path) or not os.listdir(self.src_path):
            print("[!] Source files missing. Attempting emergency submodule update...")
            try:
                subprocess.run(["git", "submodule", "update", "--init", "--recursive", "--depth", "1"], check=True)
            except Exception as e:
                print(f"[!] Emergency update failed: {e}")

    def index_functions(self):
        print(f"[>] Scanning: {self.src_path}")
        def_pat = re.compile(r'^([\w\s\*]+?)\b(func_[A-Z0-9_]+)\s*\(([^)]*)\)\s*\{', re.MULTILINE)
        
        found_count = 0
        for root, _, files in os.walk(self.src_path):
            for file in files:
                if file.endswith('.c'):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            for match in def_pat.finditer(content):
                                ret_type, name, params = match.groups()
                                ret_type = " ".join(ret_type.split()).replace("static ", "").replace("inline ", "")
                                self.function_map[name] = f"extern {ret_type} {name}({params.strip()});"
                                found_count += 1
                    except Exception:
                        continue
        print(f"[>] Indexed {found_count} raw function instances.")

    def execute(self):
        self.ensure_submodules()
        if not os.path.exists(self.src_path):
            print(f"[!!] FATAL: Path {self.src_path} still does not exist.")
            os._exit(1)
            
        self.index_functions()
        # ... (rest of header writing logic remains the same)

if __name__ == "__main__":
    SourceHarmonizerV7540().execute()
