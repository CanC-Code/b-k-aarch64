#!/usr/bin/env python3
import os
import sys
from pathlib import Path

"""
PrepareSource v2.2 — Submodule Verification
═══════════════════════════════════════════════════════════════════════════════
FIX: Added explicit verification for the decomp-files directory.
If the submodule content is missing, the script will now report exactly
what is missing instead of crashing with a FileNotFoundError.
═══════════════════════════════════════════════════════════════════════════════
"""

class PrepareSource:
    def __init__(self):
        # Resolve the root directory of the repository
        self.repo_root = Path(__file__).resolve().parent.parent
        self.decomp_root = self.repo_root / "decomp-files"
        
        # Target header path
        self.target_header = self.decomp_root / "include" / "2.0L" / "PR" / "ultratypes.h"

    def verify_environment(self):
        print(f"[>] Repo Root: {self.repo_root}")
        print(f"[>] Decomp Root: {self.decomp_root}")
        
        # Check if the decomp-files directory actually contains content
        if not self.target_header.exists():
            print(f"[!] Critical Error: Required header not found at {self.target_header}")
            print(f"    Check if the 'decomp-files' submodule is initialized and populated.")
            sys.exit(1)

    def sanitize_headers(self):
        """Removes incompatible hardware-specific macros for AArch64 builds."""
        print(f"[>] Sanitizing {self.target_header.name} for AArch64 compatibility...")
        
        try:
            content = self.target_header.read_text(encoding='utf-8')
            # Disable specific MIPS-only alignment pragmas
            new_content = content.replace("#pragma align", "// #pragma align")
            
            if new_content != content:
                self.target_header.write_text(new_content, encoding='utf-8')
                print(f"    - Cleaned successfully.")
            else:
                print(f"    - No changes needed.")
        except Exception as e:
            print(f"    - Failed to sanitize: {e}")
            sys.exit(1)

    def run(self):
        self.verify_environment()
        self.sanitize_headers()
        print("[+] Source preparation complete.")

if __name__ == "__main__":
    PrepareSource().run()
