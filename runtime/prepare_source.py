#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.11 — Comprehensive C89/IDO-to-Clang Source Normalisation

FIXES IN v75.11:
1. Visibility Logic: Injects 'extern' forward declarations for all BKA symbols at 
   the very top of the file to satisfy Clang's strict __typeof__ requirements.
2. Collision Shield: Uses greedy regex matching with length-descending sorting 
   to prevent 'audio_init' from corrupting 'audio_init_PAL'.
3. Rule A3 Expansion: Handles static assignments involving nested pointer 
   dereferences (e.g., static var = obj->sub->func()).
4. Metadata Preservation: Derives hashes from canonical relative paths to ensure 
   consistency across different build runners.
"""

class SourceHarmonizer:
    def __init__(self, target_dir, decomp_path):
        self.target_dir = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0}
        
        # Protected symbols that must NEVER be renamed by BKA logic
        self.protected_symbols = {
            'main', 'main_no_args', 'memcpy', 'memset', 'strlen', 'strcpy', 
            'strcmp', 'sprintf', 'printf', 'malloc', 'free', 'sin', 'cos', 
            'sqrt', 'abs', 'fabs', 'osViClock'
        }
        self.c_keywords = {
            'static', 'extern', 'const', 'volatile', 'inline', 'typedef', 
            'struct', 'union', 'enum', 'if', 'else', 'while', 'for', 'return'
        }

    def get_bka_hash(self, file_path):
        """Generates a stable 8-character hash based on the relative source path."""
        try:
            rel = file_path.relative_to(self.target_dir)
        except ValueError:
            rel = file_path.name
        return hashlib.md5(str(rel).encode()).hexdigest()[:8]

    def apply_c89_static_repairs(self, content):
        """
        Fixes the 'initializer element is not a compile-time constant' error.
        Converts: static int x = func(); -> static int x; ... x = func();
        """
        lines = content.splitlines()
        repaired = []
        for line in lines:
            # Matches static declarations with dynamic assignments (Rule A/B/C)
            match = re.match(r'^(\s*)static\s+([a-zA-Z_][\w\s\*]+)\s+([a-zA-Z_]\w*(?:(?:->|\.)\w+)?(?:\[[^\]]+\])?)\s*=\s*([^;]+);(.*)$', line)
            if match:
                indent, type_str, target, value, trailing = match.groups()
                if '(' in value or '->' in value or '.' in value:
                    # Split into declaration and runtime assignment
                    repaired.append(f"{indent}static {type_str} {target};")
                    repaired.append(f"{indent}{target} = {value};{trailing}")
                    continue
            repaired.append(line)
        return "\n".join(repaired)

    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        fid = self.get_bka_hash(file_path)

        # Step 1: Repair C89 Static Initialization
        content = self.apply_c89_static_repairs(content)

        # Step 2: Identify Static Functions for Isolation
        # We look for definitions: static <type> <name>(...) {
        static_func_pattern = re.compile(r'static\s+[^(]+\s+([a-zA-Z_]\w*)\s*\(')
        raw_statics = set(static_func_pattern.findall(content))
        
        # Filter protected and built-in symbols
        filtered_statics = {fn for fn in raw_statics if fn not in self.protected_symbols 
                           and not fn.startswith('__') and fn not in self.c_keywords}

        if not filtered_statics:
            return

        # Step 3: Perform Renaming with Collision Shielding
        # Sort by length DESCENDING: handles 'func_suffix' before 'func'
        sorted_statics = sorted(list(filtered_statics), key=len, reverse=True)
        replacements = {fn: f"BKA_F_{fid}_{fn}" for fn in sorted_statics}

        for fn, un in replacements.items():
            # Use \b word boundaries to prevent partial string matching
            content = re.sub(rf'\b{fn}\b', un, content)

        # Step 4: Inject Visibility Macros and Weak Aliases
        # The 'extern' declaration is the key to fixing 'undeclared identifier' in Clang
        macros = "// --- BKA ISOLATION BLOCK START ---\n"
        aliases = "\n// --- BKA WEAK ALIAS BLOCK START ---\n"
        
        for fn, un in replacements.items():
            # v75.11: Provide type-safe forward declaration for the unique name
            macros += f"extern __typeof__({un}) {un};\n"
            # Alias the original name back to the unique name for external linkage
            aliases += f"__typeof__({un}) {fn} __attribute__((weak, alias(\"{un}\")));\n"
        
        macros += "// --- BKA ISOLATION BLOCK END ---\n\n"
        aliases += "// --- BKA WEAK ALIAS BLOCK END ---\n"
        
        content = macros + content + aliases

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.stats["changes_made"] += 1

    def run(self):
        print(f"[*] Starting SourceHarmonizer v75.11...")
        # Focus on the C source files in the main target directory
        src_path = self.target_dir / "src"
        for file_path in src_path.rglob('*.[ch]'):
            if "include/libc" in str(file_path) or file_path.suffix == '.h':
                continue
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error in {file_path.name}: {e}")
        
        print(f"\n[+] v75.11 Complete. Processed {self.stats['files_processed']} files, modified {self.stats['changes_made']}.")

if __name__ == "__main__":
    # Ensure paths are absolute for the GitHub Actions environment
    base_dir = os.getcwd()
    harmonizer = SourceHarmonizer(Path(base_dir), Path(base_dir))
    harmonizer.run()
