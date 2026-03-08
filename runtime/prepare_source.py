#!/usr/bin/env python3
import os
import sys
from pathlib import Path

"""
PrepareSource v2.4 — Absolute Path Enforcement
═══════════════════════════════════════════════════════════════════════════════
LOG 60/61 — FileNotFoundError.
This version uses the current working directory as the anchor to match the
'ls -R' structure provided.
═══════════════════════════════════════════════════════════════════════════════
"""

class PrepareSource:
    def __init__(self):
        # Anchor to the current working directory (project root)
        self.cwd = Path(os.getcwd())
        
        # Based on your ls -R, decomp-files is in the root
        self.decomp_root = self.cwd / "decomp-files"
        
        # Define the exact path found in your directory listing
        self.target_header = self.decomp_root / "include" / "2.0L" / "PR" / "ultratypes.h"

    def verify_environment(self):
        print(f"[>] Working Directory: {self.cwd}")
        print(f"[>] Looking for header at: {self.target_header}")
        
        if not self.target_header.exists():
            print("[!] CRITICAL ERROR: ultratypes.h not found!")
            print("[>] Listing contents of decomp-files/include to verify:")
            inc_path = self.decomp_root / "include"
            if inc_path.exists():
                for item in inc_path.iterdir():
                    print(f"    - {item.name}")
            else:
                print("    - /decomp-files/include directory does not exist.")
            sys.exit(1)

    def sanitize_headers(self):
        """Patches N64 headers to allow AArch64/Android NDK compilation."""
        print(f"[>] Patching {self.target_header.name}...")
        try:
            content = self.target_header.read_text(encoding='utf-8')
            
            # 1. Comment out MIPS-specific pragmas that cause NDK errors
            patched_content = content.replace("#pragma align", "// #pragma align")
            
            # 2. Fix potential redefinition of basic types if they clash with NDK
            # (Adding common AArch64 fixes here)
            if "ifndef _ULTRATYPES_H_" not in patched_content:
                patched_content = "#ifndef _ULTRATYPES_H_\n#define _ULTRATYPES_H_\n" + patched_content + "\n#endif"

            if patched_content != content:
                self.target_header.write_text(patched_content, encoding='utf-8')
                print("    - Successfully applied AArch64 compatibility patches.")
            else:
                print("    - Header already patched or no changes needed.")
        except Exception as e:
            print(f"[!] IO Error: {e}")
            sys.exit(1)

    def run(self):
        self.verify_environment()
        self.sanitize_headers()
        print("[+] Environment harmonized for NDK build.")

if __name__ == "__main__":
    PrepareSource().run()
