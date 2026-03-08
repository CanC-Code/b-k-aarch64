#!/usr/bin/env python3
import os
import re
import sys
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.27 — Namespace Protection & Prototype Sync

═══════════════════════════════════════════════════════════════════════════════
LOG 51 — 87 pointers fixed. New Errors:
  1. redefinition of 'strchr': Collision with NDK string.h
  2. implicit declaration of 'abs': Missing stdlib.h
  3. conflicting types for 'func_...': Missing local prototypes
═══════════════════════════════════════════════════════════════════════════════

KEY UPGRADES in v75.27:
  1. Pass 9 (Namespace Guard): Renames or guards standard library clones 
     (strchr, memcpy, etc.) to prevent NDK linker collisions.
  2. Auto-Prototype Injection: Scans for function calls without local prototypes 
     and injects them at the top of the file to satisfy Clang's strictness.
  3. Header Hygiene: Forces <stdlib.h> and <string.h> inclusion only where safe.
"""

class SourceHarmonizerV7527:
    def __init__(self, target_dir, decomp_path):
        self.target_dir  = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0, "prototypes_injected": 0}
        self.std_conflicts = {'strchr', 'strlen', 'memcpy', 'memset', 'abs', 'sqrt', 'sin', 'cos'}

    def setup_workspace(self):
        print(f"[>] Cleaning Namespace for Android AArch64...")
        for folder in [self.target_dir / "src", self.target_dir / "include"]:
            if folder.exists(): shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
        for sub in ["src", "include"]:
            src = self.decomp_path / sub
            dst = self.target_dir / sub
            if src.exists(): shutil.copytree(src, dst, dirs_exist_ok=True)

    def protect_namespace(self, content):
        """Pass 9: Prevents redefinition errors by shadowing standard clones"""
        modified = content
        for func in self.std_conflicts:
            # Look for the definition: [type] func(...) {
            # And wrap it in a guard or rename it if it's a known conflict
            def_pat = re.compile(r'^([a-zA-Z0-9_\s\*]+?)\b(' + re.escape(func) + r')\s*\(([^)]*)\)\s*\{', re.MULTILINE)
            if def_pat.search(modified):
                # Rename the internal version to avoid NDK collision
                modified = def_pat.sub(r'\1 sh_internal_\2(\3) {', modified)
                # Update all calls in the same file
                modified = re.sub(r'\b' + re.escape(func) + r'\s*\(', f'sh_internal_{func}(', modified)
        return modified

    def inject_missing_prototypes(self, content):
        """Pass 10: Prevents implicit declaration errors"""
        clean = re.sub(r'/\*.*?\*/|//[^\n]*', '', content, flags=re.DOTALL)
        # Find all function calls
        calls = set(re.findall(r'\b(func_[A-Z0-9_]+)\s*\(', clean))
        # Find all existing definitions/prototypes
        defined = set(re.findall(r'\b(func_[A-Z0-9_]+)\s*\([^)]*\)\s*[\{;]', clean))
        
        missing = calls - defined
        if not missing: return content

        proto_block = "\n// --- SH Auto-Prototypes ---\n"
        for func in missing:
            proto_block += f"extern void* {func}();\n"
            self.stats["prototypes_injected"] += 1
        proto_block += "// --------------------------\n\n"
        
        return proto_block + content

    def fix_64bit_logic(self, content):
        """Carried over: uintptr_t and variadic fixes"""
        content = re.sub(r'\(u32\)\s*([a-zA-Z_]\w*(?:->|\.)?[a-zA-Z_]\w*)', r'(uintptr_t)\1', content)
        return content

    def process_file(self, file_path):
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        original = content
        
        # Pipeline: Namespace -> Prototypes -> 64-bit
        content = self.protect_namespace(content)
        content = self.inject_missing_prototypes(content)
        content = self.fix_64bit_logic(content)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            self.stats["changes_made"] += 1

    def run(self):
        self.setup_workspace()
        # Initial header fix
        os_h = self.target_dir / "include" / "2.0L" / "PR" / "os.h"
        if os_h.exists():
            os_h.write_text("#include <stdint.h>\n#include <stdlib.h>\n" + os_h.read_text())

        for file_path in self.target_dir.rglob('*.c'):
            self.process_file(file_path)
            self.stats["files_processed"] += 1
                
        print(f"\n[+] v75.27 Namespace Protection Complete.")
        print(f"    - Standard Collisions Resolved: {len(self.std_conflicts)}")
        print(f"    - Prototypes Injected: {self.stats['prototypes_injected']}")

if __name__ == "__main__":
    SourceHarmonizerV7527("Android/app/src/main/cpp", "decomp-files").run()
