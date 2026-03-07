#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.12 — Deep Workspace Integration

CHANGES:
1. AUTO-PATH DISCOVERY: Scans the current working directory for 'src' and 'include' 
   if target paths are missing, ensuring zero-edit errors are bypassed.
2. MULTILINE STATIC MATCHING: Detects IDO-style 'static' definitions where 
   keywords and return types are separated by newlines.
3. ALIAS HOISTING: Moves the BKA Macro block to the absolute top of the file, 
   preceding even system includes if necessary, to ensure __typeof__ stability.
4. WORD-BOUNDARY REFINEMENT: Prevents collisions between 'func' and 'func_ptr' 
   using negative lookahead assertions.
"""

class SourceHarmonizer:
    def __init__(self, search_root=None):
        # Dynamic Path Resolution
        self.root = Path(search_root or os.getcwd()).resolve()
        self.src_dir = self.root / "src"
        
        # Fallback for different repo structures
        if not self.src_dir.exists():
            # Attempt to find 'src' in subdirectories (common in Android/Gradle layouts)
            possible_srcs = list(self.root.rglob("app/src/main/cpp/src"))
            if possible_srcs:
                self.src_dir = possible_srcs[0]
            else:
                # Last resort: search for any 'src' folder
                all_srcs = [p for p in self.root.glob("**/src") if "node_modules" not in str(p)]
                if all_srcs: self.src_dir = all_srcs[0]

        self.stats = {"processed": 0, "modified": 0}
        self.protected = {'main', 'main_no_args', 'memcpy', 'memset', 'osViClock', 'D_8027D008'}

    def get_bka_hash(self, file_path):
        """Generates a stable 8-character hash based on relative pathing."""
        try:
            rel = file_path.relative_to(self.root)
        except ValueError:
            rel = file_path.name
        return hashlib.md5(str(rel).encode()).hexdigest()[:8]

    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        fid = self.get_bka_hash(file_path)

        # 1. C89 Logic Repair: Fix static assignments at file scope
        lines = content.splitlines()
        repaired = []
        for line in lines:
            # Match: static [type] var = [dynamic_val];
            match = re.match(r'^(\s*)static\s+([a-zA-Z_][\w\s\*]+)\s+([a-zA-Z_]\w*)\s*=\s*([^;]+);(.*)$', line)
            if match and ('(' in match.group(4) or '->' in match.group(4)):
                indent, t, var, val, trail = match.groups()
                repaired.append(f"{indent}static {t} {var};")
                repaired.append(f"{indent}{var} = {val};{trail}")
            else:
                repaired.append(line)
        content = "\n".join(repaired)

        # 2. Advanced Static Function Identification
        # This regex handles cases where 'static' and the function name are separated by whitespace/newlines
        static_pattern = re.compile(r'static\s+(?:[a-zA-Z_]\w*\s+)+(?:\*+\s*)?([a-zA-Z_]\w*)\s*\(')
        found_statics = set(static_pattern.findall(content))
        
        # Filter protected symbols
        targets = {fn for fn in found_statics if fn not in self.protected and not fn.startswith('__')}

        if targets:
            # Sort by length DESC to protect against substring corruption
            sorted_targets = sorted(list(targets), key=len, reverse=True)
            replacements = {fn: f"BKA_F_{fid}_{fn}" for fn in sorted_targets}

            # 3. Controlled Renaming
            for fn, un in replacements.items():
                content = re.sub(rf'\b{fn}\b(?!\s*->|\s*\.)', un, content)

            # 4. Injection of Forward Declarations and Aliases
            macros = "// --- BKA v75.12 START ---\n"
            aliases = "\n// --- BKA v75.12 ALIASES ---\n"
            for fn, un in replacements.items():
                macros += f"extern __typeof__({un}) {un};\n"
                aliases += f"__typeof__({un}) {fn} __attribute__((weak, alias(\"{un}\")));\n"
            
            macros += "// --- BKA v75.12 END ---\n\n"
            content = macros + content + aliases

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.stats["modified"] += 1

    def run(self):
        if not self.src_dir or not self.src_dir.exists():
            print(f"[!] Critical Error: Could not locate 'src' directory in {self.root}")
            print("[!] Current directory contents:", os.listdir(os.getcwd()))
            return

        print(f"[*] Targeting Source Tree: {self.src_dir}")
        for file_path in self.src_dir.rglob("*.[ch]"):
            if "include/libc" in str(file_path): continue
            try:
                self.process_file(file_path)
                self.stats["processed"] += 1
            except Exception as e:
                print(f"[!] Error in {file_path.name}: {e}")

        print(f"\n[+] v75.12 Execution Summary:")
        print(f"    - Files Analyzed: {self.stats['processed']}")
        print(f"    - Files Modified: {self.stats['modified']}")

if __name__ == "__main__":
    harmonizer = SourceHarmonizer()
    harmonizer.run()
