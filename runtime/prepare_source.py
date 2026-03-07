#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.10 — Comprehensive C89/IDO-to-Clang Source Normalisation

FIXES:
- Injects 'extern' forward declarations to resolve "undeclared identifier" in weak aliases.
- Uses descending length sorting for symbols to prevent substring corruption.
- Derives unique hashes from relative paths to ensure absolute isolation.
"""

class SourceHarmonizer:
    def __init__(self, target_dir, decomp_path):
        self.target_dir = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0}

    def get_bka_hash(self, file_path):
        # Unique hash based on file's relative path
        relative_path = file_path.relative_to(self.target_dir)
        return hashlib.md5(str(relative_path).encode()).hexdigest()[:8]

    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        file_hash = self.get_bka_hash(file_path)
        static_func_pattern = re.compile(r"static\s+[^(]+\s+([a-zA-Z0-9_]+)\s*\(")
        static_funcs = set(static_func_pattern.findall(original_content))
        static_funcs = {fn for fn in static_funcs if not fn.startswith("__")}

        if not static_funcs:
            return

        # v75.10 FIX: Sort by length DESCENDING to prevent substring collisions
        sorted_funcs = sorted(list(static_funcs), key=len, reverse=True)
        replacements = {fn: f"BKA_F_{file_hash}_{fn}" for fn in sorted_funcs}

        modified = original_content
        for fn, un in replacements.items():
            modified = re.sub(rf"\b{fn}\b", un, modified)

        # v75.10 FIX: Inject 'extern' forward-decls for visibility
        macros = "// --- BKA MACROS START ---\n"
        aliases = "\n// --- BKA ALIASES START ---\n"
        
        for fn, un in replacements.items():
            macros += f"extern __typeof__({un}) {un};\n"
            aliases += f"__typeof__({un}) {fn} __attribute__((weak, alias(\"{un}\")));\n"

        macros += "// --- BKA MACROS END ---\n\n"
        aliases += "// --- BKA ALIASES END ---\n"

        new_content = macros + modified + aliases

        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            self.stats["changes_made"] += 1

    def run(self):
        print(f"[*] Applying v75.10 Linker Isolation to {self.target_dir}...")
        for file_path in self.target_dir.rglob('*.[ch]'):
            if "include/libc" in str(file_path) or file_path.suffix == '.h':
                continue
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")
        
        print(f"\n[+] v75.10 Complete. Modified {self.stats['changes_made']} files.")

if __name__ == "__main__":
    target = os.path.join(os.getcwd(), "src")
    harmonizer = SourceHarmonizer(target, os.getcwd())
    harmonizer.run()
