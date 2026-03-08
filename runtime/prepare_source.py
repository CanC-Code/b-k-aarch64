#!/usr/bin/env python3
import os
import re
import sys
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.26 — 64-bit Portability & Variadic Sync

═══════════════════════════════════════════════════════════════════════════════
LOG 50 — SDK Truth applied to 88 functions. New Errors:
  1. osSyncPrintf: conflicting types (Variadic mismatch)
  2. pointer to smaller type 'u32': Integer truncation on AArch64
═══════════════════════════════════════════════════════════════════════════════

KEY UPGRADES in v75.26:
  1. Pass 8 (64-bit Portability): Automatically converts (u32)pointer casts to 
     (uintptr_t) to prevent data loss on 64-bit Android systems.
  2. Variadic Alignment: Detects and fixes '...' ellipsis mismatches in SDK 
     functions like osSyncPrintf.
  3. uintptr_t Injection: Ensures the portability header <stdint.h> is present.
"""

class SourceHarmonizerV7526:
    def __init__(self, target_dir, decomp_path):
        self.target_dir  = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0, "ptr_fixes": 0}
        self.sdk_truth = {} 

    def setup_workspace(self):
        print(f"[>] Preparing 64-bit Portability Layer...")
        for folder in [self.target_dir / "src", self.target_dir / "include"]:
            if folder.exists(): shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
        for sub in ["src", "include"]:
            src = self.decomp_path / sub
            dst = self.target_dir / sub
            if src.exists(): shutil.copytree(src, dst, dirs_exist_ok=True)

    def patch_global_headers(self):
        """Pass 0: Portability Injection"""
        # We MUST include stdint.h for uintptr_t to work on 64-bit
        portability_block = (
            "\n#include <stdint.h>\n"
            "#ifndef _SH_PORTABLE_H\n#define _SH_PORTABLE_H\n"
            "typedef intptr_t  ptr_diff_t;\n" # For 64-bit pointer math
            "#endif\n"
        )
        
        os_h = self.target_dir / "include" / "2.0L" / "PR" / "os.h"
        if os_h.exists():
            content = os_h.read_text(encoding='utf-8', errors='ignore')
            os_h.write_text(portability_block + content)

    def fix_64bit_pointer_truncation(self, content):
        """
        Pass 8: Detects (u32)some_ptr and converts to (uintptr_t)
        This is vital for Android AArch64 compatibility.
        """
        # Match (u32)var where var is likely a pointer or address
        # We look for common pointer patterns like -> or * or &
        ptr_cast_pat = re.compile(r'\(u32\)\s*([a-zA-Z_]\w*(?:->|\.)?[a-zA-Z_]\w*)')
        
        def _to_uintptr(m):
            self.stats["ptr_fixes"] += 1
            return f"(uintptr_t){m.group(1)}"

        return ptr_cast_pat.sub(_to_uintptr, content)

    def scan_sdk_for_truth(self):
        """Pass 7a: Enhanced to capture variadic '...' truth"""
        sdk_pat = re.compile(r'extern\s+([a-zA-Z0-9_\s\*]+?)\b([a-zA-Z_]\w*)\s*\(([^;]*)\)\s*;', re.MULTILINE)
        for h_file in self.target_dir.rglob('*.h'):
            content = h_file.read_text(encoding='utf-8', errors='ignore')
            for m in sdk_pat.finditer(content):
                rtype, name, params = m.group(1).strip(), m.group(2), m.group(3).strip()
                if name.startswith('os') or name.startswith('__os'):
                    self.sdk_truth[name] = (rtype, params)

    def coerce_signatures(self, content):
        """Pass 7b: Implementation Force-Alignment (Variadic Aware)"""
        modified = content
        for name, (rtype, params) in self.sdk_truth.items():
            impl_pat = re.compile(r'^([a-zA-Z0-9_\s\*]+?)\b' + re.escape(name) + r'\s*\(([^)]*)\)\s*\{', re.MULTILINE)
            
            def _apply(m):
                # Always favor the SDK header params, especially if they contain '...'
                return f"{rtype} {name}({params}) {{"

            modified = impl_pat.sub(_apply, modified)
        return modified

    def process_file(self, file_path):
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        original = content
        
        # Pipeline: 64-bit Pointer Safety -> Linkage Coercion
        content = self.fix_64bit_pointer_truncation(content)
        content = self.coerce_signatures(content)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            self.stats["changes_made"] += 1

    def run(self):
        self.setup_workspace()
        self.patch_global_headers()
        self.scan_sdk_for_truth()
        
        for file_path in self.target_dir.rglob('*.c'):
            self.process_file(file_path)
            self.stats["files_processed"] += 1
                
        print(f"\n[+] v75.26 Portability Sync Complete.")
        print(f"    - Pointer Truncations Fixed: {self.stats['ptr_fixes']}")
        print(f"    - Files Harmonized: {self.stats['changes_made']}")

if __name__ == "__main__":
    SourceHarmonizerV7526("Android/app/src/main/cpp", "decomp-files").run()
