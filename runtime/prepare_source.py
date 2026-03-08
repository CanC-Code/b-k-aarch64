#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

"""
PrepareSource v2.1 — Path Logic Correction
═══════════════════════════════════════════════════════════════════════════════
FIX: Removed CMake ${DECOMP_ROOT} syntax which caused SyntaxError.
Ensures paths are resolved relative to the script location on the GitHub runner.
═══════════════════════════════════════════════════════════════════════════════
"""

class PrepareSource:
    def __init__(self):
        # Resolve the root directory of the repository
        # This script is in /runtime/, so we go up one level
        self.repo_root = Path(__file__).resolve().parent.parent
        self.decomp_root = self.repo_root / "decomp-files"
        
        # Define paths that were previously causing errors
        self.include_path_20L = self.decomp_root / "include" / "2.0L"
        self.pr_include_path = self.include_path_20L / "PR"

    def verify_environment(self):
        print(f"[>] Repo Root: {self.repo_root}")
        print(f"[>] Decomp Root: {self.decomp_root}")
        
        if not self.decomp_root.exists():
            print(f"[!] Error: {self.decomp_root} not found. Submodules may not be initialized.")
            sys.exit(1)

    def sanitize_headers(self):
        """Removes incompatible hardware-specific macros for AArch64 builds."""
        print("[>] Sanitizing N64 headers for AArch64 compatibility...")
        
        target_header = self.pr_include_path / "ultratypes.h"
        if target_header.exists():
            try:
                content = target_header.read_text(encoding='utf-8')
                # Example: Disable specific MIPS-only alignment pragmas
                new_content = content.replace("#pragma align", "// #pragma align")
                if new_content != content:
                    target_header.write_text(new_content, encoding='utf-8')
                    print(f"    - Cleaned: {target_header.name}")
            except Exception as e:
                print(f"    - Failed to sanitize {target_header.name}: {e}")

    def run(self):
        self.verify_environment()
        self.sanitize_headers()
        print("[+] Source preparation complete.")

if __name__ == "__main__":
    PrepareSource().run()
