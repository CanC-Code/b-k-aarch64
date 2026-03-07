#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.10 — Full Production Build
Fixes:
1. Substring Collision: Sorts by name length so 'func_PAL' isn't ruined by 'func'.
2. Undeclared Identifier: Injects 'extern' decls before 'weak alias' blocks.
3. Rule A2: Retains support for C89 static struct member initialization.
"""

class SourceHarmonizer:
    def __init__(self, target_dir, decomp_path):
        self.target_dir = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0}
        
        self.c_keywords = {'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do', 
                          'break', 'continue', 'case', 'default', 'goto', 'struct', 'union', 
                          'enum', 'static', 'extern', 'const', 'volatile', 'inline', 'typedef'}
        
        self.std_c = {'main', 'main_no_args', 'memcpy', 'memset', 'strlen', 'strcpy', 'strcmp'}
        self.sdk_prefixes = ('os', 'gu', 'al', 'gS', 'gD', 'gd', '__os')

    def setup_workspace(self):
        src_target = self.target_dir / "src"
        include_target = self.target_dir / "include"
        for folder in [src_target, include_target]:
            if folder.exists(): shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.decomp_path / "src", src_target, dirs_exist_ok=True)
        shutil.copytree(self.decomp_path / "include", include_target, dirs_exist_ok=True)

    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        fid = hashlib.md5(str(file_path.name).encode()).hexdigest()[:8]
        
        # 1. Fix IDO Array Initializers (Rule A1)
        content = re.sub(r'^([ \t]*[a-zA-Z_]\w*(?:\s*\*)*)\s+([a-zA-Z_]\w*)\s*\[\s*(\d+)\s*\]\s*=\s*([a-zA-Z_]\w*)\s*;',
                         r'\1 \2[\3]; __builtin_memcpy(\2, \4, \3 * sizeof(\1));', content, flags=re.MULTILINE)

        # 2. Fix Static Struct Member Assignments (Rule A2)
        content = re.sub(r'static\s+([a-zA-Z_]\w*->[a-zA-Z_]\w*(?:\[[^\]]+\])?)\s*=', r'\1 =', content)

        # 3. Identify Static Functions for Alias Isolation
        clean_code = re.sub(r'//.*|/\*.*?\*/|(?s)".*?"', '', content)
        static_func_pattern = re.compile(r'\bstatic\s+[^(]+\s+([a-zA-Z0-9_]+)\s*\(')
        found_funcs = set(static_func_pattern.findall(clean_code))
        
        # Filter exclusions
        valid_funcs = [f for f in found_funcs if f not in self.c_keywords and f not in self.std_c 
                       and not f.startswith(self.sdk_prefixes) and not f.isupper()]
        
        # CRITICAL FIX: Sort by length descending to prevent partial replacement of _PAL suffixes
        valid_funcs.sort(key=len, reverse=True)

        if not valid_funcs:
            with open(file_path, 'w') as f: f.write(content)
            return

        replacements = {fn: f"BKA_F_{fid}_{fn}" for fn in valid_funcs}
        
        # Apply renaming with word boundaries
        for fn, un in replacements.items():
            content = re.sub(rf'\b{fn}\b', un, content)

        # 4. Generate Header/Footer Blocks
        macros = "// --- BKA MACROS START ---\n"
        aliases = "\n// --- BKA ALIASES START ---\n"
        
        for fn, un in replacements.items():
            # Injected forward declaration ensures __typeof__ has a target (Fixes your log error)
            macros += f"extern __typeof__({un}) {un};\n"
            # Weak alias links the original name back to the unique one
            aliases += f"__typeof__({un}) {fn} __attribute__((weak, alias(\"{un}\")));\n"

        macros += "// --- BKA MACROS END ---\n\n"
        aliases += "// --- BKA ALIASES END ---\n"

        with open(file_path, 'w') as f:
            f.write(macros + content + aliases)
        self.stats["changes_made"] += 1

    def run(self):
        self.setup_workspace()
        print(f"[*] Harmonizing {self.target_dir}...")
        for file_path in self.target_dir.rglob('*.[ch]'):
            if "include/libc" in str(file_path) or file_path.suffix == '.h': continue
            self.process_file(file_path)
            self.stats["files_processed"] += 1
        print(f"[+] Done. Modified {self.stats['changes_made']} files.")

if __name__ == "__main__":
    # Ensure these paths match your Runner environment
    harmonizer = SourceHarmonizer("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
