#!/usr/bin/env python3
import os
import re
import subprocess
from pathlib import Path

"""
SourceHarmonizer v75.45 — Absolute Path Normalization
═══════════════════════════════════════════════════════════════════════════════
LOG 68 — Fixed path resolution for GitHub Actions environments.
═══════════════════════════════════════════════════════════════════════════════
"""

class SourceHarmonizerV7545:
    def __init__(self):
        # Explicitly target the runner's workspace root
        self.workspace = Path(os.getenv('GITHUB_WORKSPACE', os.getcwd())).resolve()
        self.src_path = self.workspace / "decomp-files" / "src"
        self.function_map = {}

    def verify_sources(self):
        """Checks for source files and attempts a deep repair if missing."""
        if not self.src_path.exists() or not any(self.src_path.iterdir()):
            print(f"[!] Target missing at: {self.src_path}")
            print("[>] Attempting recursive submodule repair...")
            try:
                subprocess.run([
                    "git", "submodule", "update", "--init", "--recursive", "--force"
                ], cwd=self.workspace, check=True)
            except Exception as e:
                print(f"[!!] Repair failed: {e}")

    def index_functions(self):
        print(f"[>] Indexing from: {self.src_path}")
        # Pattern for standard function definitions
        def_pat = re.compile(r'^([\w\s\*]+?)\b(func_[A-Z0-9_]+)\s*\(([^)]*)\)\s*\{', re.MULTILINE)
        
        found_count = 0
        for c_file in self.src_path.rglob("*.c"):
            try:
                content = c_file.read_text(encoding='utf-8', errors='ignore')
                for match in def_pat.finditer(content):
                    ret_type, name, params = match.groups()
                    # Clean return type
                    ret_type = " ".join(ret_type.split()).replace("static ", "").replace("inline ", "")
                    self.function_map[name] = f"extern {ret_type} {name}({params.strip()});"
                    found_count += 1
            except Exception:
                continue
        
        if found_count == 0:
            print("[!!] FATAL: No functions indexed. Check submodule content.")
            os._exit(1)
        print(f"[>] Successfully indexed {found_count} functions.")

    def execute(self):
        self.verify_sources()
        self.index_functions()

if __name__ == "__main__":
    SourceHarmonizerV7545().execute()
