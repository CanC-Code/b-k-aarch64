#!/usr/bin/env python3
import os
import re
import sys
import hashlib
from pathlib import Path

"""
SourceHarmonizer v75.13 — Absolute CI/CD Workspace Anchoring

FIXES:
1. GITHUB_WORKSPACE INTEGRATION: Uses environment variables to find the code,
   eliminating "zero-edit" errors caused by relative pathing in CI runners.
2. MULTI-LINE C89 REPAIR: Fixes static assignments that span multiple lines,
   common in legacy IDO decompilations.
3. TYPE-SAFE ALIASING: Explicitly declares the BKA symbol before the alias
   to satisfy Clang's strict symbol visibility checks.
"""

class SourceHarmonizer:
    def __init__(self):
        # Anchor to the GitHub Actions workspace or current directory
        workspace = os.getenv('GITHUB_WORKSPACE', os.getcwd())
        self.root = Path(workspace).resolve()
        
        # Define search targets within the repository
        self.search_dirs = [
            self.root / "src",
            self.root / "app/src/main/cpp"
        ]
        
        self.stats = {"processed": 0, "modified": 0}
        self.protected = {'main', 'memcpy', 'memset', 'osViClock'}

    def get_bka_hash(self, file_path):
        try:
            rel = file_path.relative_to(self.root)
        except ValueError:
            rel = file_path.name
        return hashlib.md5(str(rel).encode()).hexdigest()[:8]

    def repair_c89_statics(self, content):
        """
        Splits: static type var = dynamic_init(); 
        Into:   static type var; ... var = dynamic_init();
        """
        # Improved regex to handle optional pointers and whitespace
        pattern = re.compile(r'^(\s*)static\s+([a-zA-Z_][\w\s\*]+)\s+([a-zA-Z_]\w*)\s*=\s*([^;]+);', re.MULTILINE)
        
        def subst(match):
            indent, dtype, var, val = match.groups()
            # Only repair if the initializer is not a simple constant
            if any(c in val for c in ('(', '->', '.', '[')):
                return f"{indent}static {dtype} {var};\n{indent}{var} = {val};"
            return match.group(0)

        return pattern.sub(subst, content)

    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original = content
        fid = self.get_bka_hash(file_path)

        # 1. Apply C89 Static Repairs
        content = self.repair_c89_statics(content)

        # 2. Identify and Rename Static Functions
        static_pattern = re.compile(r'static\s+(?:[a-zA-Z_]\w*\s+)+(?:\*+\s*)?([a-zA-Z_]\w*)\s*\(')
        targets = set(static_pattern.findall(content)) - self.protected
        
        if targets:
            sorted_targets = sorted(list(targets), key=len, reverse=True)
            replacements = {fn: f"BKA_F_{fid}_{fn}" for fn in sorted_targets}

            # Rename using word boundaries
            for fn, un in replacements.items():
                content = re.sub(rf'\b{fn}\b(?!\s*->|\s*\.)', un, content)

            # 3. Inject Visibility Macros at the top
            headers = "// --- BKA v75.13 VISIBILITY ---\n"
            footer = "\n// --- BKA v75.13 ALIASES ---\n"
            for fn, un in replacements.items():
                headers += f"extern __typeof__({un}) {un};\n"
                footer += f"__typeof__({un}) {fn} __attribute__((weak, alias(\"{un}\")));\n"
            
            content = headers + "\n" + content + footer

        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.stats["modified"] += 1

    def run(self):
        print(f"[*] Starting v75.13. Workspace: {self.root}")
        found_any = False
        
        for d in self.search_dirs:
            if not d.exists(): continue
            found_any = True
            print(f"[*] Processing directory: {d}")
            for file_path in d.rglob("*.[ch]"):
                if "include/libc" in str(file_path): continue
                try:
                    self.process_file(file_path)
                    self.stats["processed"] += 1
                except Exception as e:
                    print(f"[!] Error: {e}")

        if not found_any:
            print(f"[!] Warning: No source directories found in {self.root}")
            print(f"[!] Listing workspace: {os.listdir(self.root)}")

        print(f"\n[+] v75.13 Complete. Modified {self.stats['modified']} of {self.stats['processed']} files.")

if __name__ == "__main__":
    SourceHarmonizer().run()
