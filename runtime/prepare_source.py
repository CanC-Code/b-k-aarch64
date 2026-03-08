#!/usr/bin/env python3
import os
import re
import sys
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.28 — Global Foundation Injection

═══════════════════════════════════════════════════════════════════════════════
LOG 52 — Subsystems (BGS, core1) hitting 'uintptr_t' errors and 'abs' collisions.
═══════════════════════════════════════════════════════════════════════════════

KEY UPGRADES in v75.28:
  1. Foundation Header: Creates 'include/sh_foundation.h' with all 64-bit types.
  2. Forced Inclusion: Injects '#include "sh_foundation.h"' at the very top 
     of every single .c file to ensure 'uintptr_t' is always known.
  3. Weak Linkage Strategy: Automatically marks all game-defined standard 
     clones (abs, memcpy, strchr) as 'weak' to resolve NDK collisions.
"""

class SourceHarmonizerV7528:
    def __init__(self, target_dir, decomp_path):
        self.target_dir  = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0, "weak_applied": 0}
        self.std_clones = {'abs', 'strchr', 'strlen', 'memcpy', 'memset', 'sqrt', 'sin', 'cos'}

    def setup_workspace(self):
        print(f"[>] Constructing Global Foundation...")
        for folder in [self.target_dir / "src", self.target_dir / "include"]:
            if folder.exists(): shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
        for sub in ["src", "include"]:
            src = self.decomp_path / sub
            dst = self.target_dir / sub
            if src.exists(): shutil.copytree(src, dst, dirs_exist_ok=True)

    def create_foundation_header(self):
        """Creates the absolute source of truth for types and NDK compatibility."""
        foundation = (
            "#ifndef SH_FOUNDATION_H\n#define SH_FOUNDATION_H\n\n"
            "#include <stdint.h>\n#include <stddef.h>\n#include <stdlib.h>\n\n"
            "// N64 Standard Types\n"
            "typedef int8_t   s8;  typedef uint8_t  u8;\n"
            "typedef int16_t  s16; typedef uint16_t u16;\n"
            "typedef int32_t  s32; typedef uint32_t u32;\n"
            "typedef int64_t  s64; typedef uint64_t u64;\n"
            "typedef float    f32; typedef double   f64;\n\n"
            "// 64-bit Portability\n"
            "typedef intptr_t ptrdiff_t_sh;\n\n"
            "#endif\n"
        )
        (self.target_dir / "include" / "sh_foundation.h").write_text(foundation)

    def apply_weak_linkage(self, content):
        """Pass 11: Marks clones as weak to allow NDK versions to take priority."""
        modified = content
        for func in self.std_clones:
            # Pattern: [type] func([params]) {
            pat = re.compile(r'^([a-zA-Z0-9_\s\*]+?)\b(' + re.escape(func) + r')\s*\(([^)]*)\)\s*\{', re.MULTILINE)
            def _sub(m):
                self.stats["weak_applied"] += 1
                return f"__attribute__((weak)) {m.group(1)} {m.group(2)}({m.group(3)}) {{"
            modified = pat.sub(_sub, modified)
        return modified

    def process_file(self, file_path):
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        original = content
        
        # 1. Force Foundation Inclusion
        if 'sh_foundation.h' not in content:
            content = '#include "sh_foundation.h"\n' + content
            
        # 2. Fix Pointer Truncation (using foundation's uintptr_t)
        content = re.sub(r'\(u32\)\s*([a-zA-Z_]\w*(?:->|\.)?[a-zA-Z_]\w*)', r'(uintptr_t)\1', content)
        
        # 3. Apply Weak Linkage to standard library clones
        content = self.apply_weak_linkage(content)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            self.stats["changes_made"] += 1

    def run(self):
        self.setup_workspace()
        self.create_foundation_header()
        
        # Patch the main GBI header to use our foundation
        gbi_h = self.target_dir / "include" / "2.0L" / "PR" / "gbi.h"
        if gbi_h.exists():
            gbi_h.write_text('#include "sh_foundation.h"\n#define F3DEX_GBI_2 1\n' + gbi_h.read_text())

        for file_path in self.target_dir.rglob('*.c'):
            self.process_file(file_path)
            self.stats["files_processed"] += 1
                
        print(f"\n[+] v75.28 Global Foundation Applied.")
        print(f"    - Weak Linkage Overrides: {self.stats['weak_applied']}")
        print(f"    - Total Files Unified: {self.stats['changes_made']}")

if __name__ == "__main__":
    SourceHarmonizerV7528("Android/app/src/main/cpp", "decomp-files").run()
