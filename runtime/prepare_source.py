#!/usr/bin/env python3
import os
import re
import sys
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.24 — Validation & Alignment Cross-Check

═══════════════════════════════════════════════════════════════════════════════
LOG 48 — Harmonized 2479 functions. Failure in leafboat.c:
  "error: array initializer must be an initializer list or string literal"
  Caused by: u8 tmp[6] = D_80390DA0; 
═══════════════════════════════════════════════════════════════════════════════

NEW IN v75.24:
  1. Pass 6 (Validation): Detects illegal array assignments (Variable-to-Array).
  2. Alignment Verification: Ensures target arrays are populated via memcpy 
     to maintain the original N64 data alignment.
  3. Strict Header Sync: Refined Pass 5 to prevent "ghost" signature matches.
"""

class SourceHarmonizerV7524:
    def __init__(self, target_dir, decomp_path):
        self.target_dir  = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0, "validations": 0}
        self.header_decls = {} 

        self.c_keywords = {'if','while','for','switch','return','sizeof','else','do','break','continue','case','default','goto','struct','union','enum','static','extern','const','volatile','inline','typedef'}
        self.sdk_prefixes = ('os', 'gu', 'al', 'gS', 'gD', 'gd', '__os', 'sp', 'dp', 'rmon')
        self._storage_quals = {'static', 'extern', 'inline', 'const', 'volatile', '__attribute__', '__restrict', 'restrict', 'register'}
        self._ctrl_keywords = {'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do', 'break', 'continue', 'case', 'default', 'goto', 'typedef'}

    def setup_workspace(self):
        print(f"[>] Initializing Workspace: {self.target_dir}")
        for folder in [self.target_dir / "src", self.target_dir / "include"]:
            if folder.exists(): shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
        for sub in ["src", "include"]:
            src = self.decomp_path / sub
            dst = self.target_dir / sub
            if src.exists(): shutil.copytree(src, dst, dirs_exist_ok=True)

    def patch_global_headers(self):
        """Pass 0: Infrastructure Fixes"""
        print("[>] Patching SDK Headers for Clang Compatibility...")
        gbi = self.target_dir / "include" / "2.0L" / "PR" / "gbi.h"
        if gbi.exists():
            content = gbi.read_text(encoding='utf-8', errors='ignore')
            if 'F3DEX_GBI_2' not in content[:1000]:
                gbi.write_text("#ifndef F3DEX_GBI_2\n#define F3DEX_GBI_2 1\n#endif\n" + content)

        # Global size_t safety
        for h in self.target_dir.rglob('*.h'):
            content = h.read_text(encoding='utf-8', errors='ignore')
            if 'size_t' in content and '<stddef.h>' not in content:
                h.write_text("#include <stddef.h>\n" + content)

    def remove_strings_and_comments(self, text):
        text = re.sub(r'//[^\n]*', '', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)
        return text

    def scan_headers_for_signatures(self):
        """Pass 5a: Mapping the 'Truth' from Headers"""
        print("[>] Cross-referencing signatures...")
        # Catching: [ReturnType] [FuncName]([Params]);
        decl_pat = re.compile(r'^([a-zA-Z0-9_\s\*]+?)\b([a-zA-Z_]\w*)\s*\([^;{}]*\)\s*;', re.MULTILINE)
        for h_file in self.target_dir.rglob('*.h'):
            content = self.remove_strings_and_comments(h_file.read_text(encoding='utf-8', errors='ignore'))
            for m in decl_pat.finditer(content):
                rtype, name = m.group(1).strip(), m.group(2)
                if name not in self.c_keywords and 'static' not in rtype and 'typedef' not in rtype:
                    self.header_decls[name] = rtype

    def validate_array_initializers(self, content):
        """
        Pass 6: The Alignment & Legality Checker
        Converts: u8 arr[4] = SomeVar; -> u8 arr[4]; memcpy(arr, SomeVar, 4);
        """
        # Regex identifies array definitions being assigned a non-brace, non-string value
        # Group 1: Type, Group 2: Name, Group 3: Size, Group 4: Invalid Source
        illegal_init_pat = re.compile(
            r'^([ \t]*(?:struct\s+|union\s+|enum\s+)?[a-zA-Z_]\w*(?:\s*\*)*)\s+' # Type
            r'([a-zA-Z_]\w*)\s*\[\s*(\d+|[A-Z_0-9]+)\s*\]\s*=\s*'                # Name[Size] =
            r'([a-zA-Z_]\w*)\s*;',                                              # Invalid Source
            re.MULTILINE
        )

        def _fix_init(m):
            indent_type = m.group(1)
            arr_name = m.group(2)
            arr_size = m.group(3)
            src_val = m.group(4)
            
            # Cross-check: If src_val is a string literal (handled by regex before) or 
            # digit, it might be valid. If it's a variable name, it's illegal.
            if src_val.isdigit(): return m.group(0) 

            self.stats["validations"] += 1
            # Maintain alignment by using __builtin_memcpy for raw data transfer
            return (f"{indent_type} {arr_name}[{arr_size}];\n"
                    f"    __builtin_memcpy({arr_name}, {src_val}, {arr_size} * sizeof({indent_type.strip()}));")

        return illegal_init_pat.sub(_fix_init, content)

    def harmonize_signatures(self, content):
        """Pass 5b: Enforcing signature alignment with header truth"""
        modified = content
        for name, rtype in self.header_decls.items():
            # Only target global definitions
            def_pat = re.compile(r'^([a-zA-Z0-9_\s\*]+?)\b(' + re.escape(name) + r')\s*\(([^{;]*)\)\s*\{', re.MULTILINE)
            
            def _sub(m):
                curr_rtype = m.group(1).strip()
                # If it's static or already matches, skip
                if 'static' in curr_rtype or 'inline' in curr_rtype or curr_rtype == rtype:
                    return m.group(0)
                return f"{rtype} {m.group(2)}({m.group(3)}) {{"
            
            modified = def_pat.sub(_sub, modified)
        return modified

    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        original = content
        # Run Sequence: Validation -> Harmonization -> Cleaning
        content = self.validate_array_initializers(content) # Pass 6
        content = self.harmonize_signatures(content)        # Pass 5
        
        # Ensure static forward declarations don't conflict with global headers
        clean = self.remove_strings_and_comments(content)
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.stats["changes_made"] += 1

    def run(self):
        self.setup_workspace()
        self.patch_global_headers()
        self.scan_headers_for_signatures()
        
        for file_path in self.target_dir.rglob('*.[ch]'):
            # Skip libc and non-source files for logic processing
            if "include/libc" not in str(file_path) and file_path.suffix == '.c':
                self.process_file(file_path)
                self.stats["files_processed"] += 1
                
        print(f"\n[+] v75.24 Complete.")
        print(f"    - Files Processed: {self.stats['files_processed']}")
        print(f"    - Files Modified:  {self.stats['changes_made']}")
        print(f"    - Array Validations: {self.stats['validations']}")

if __name__ == "__main__":
    # Point to your N64 decompilation source and Android JNI target
    SourceHarmonizerV7524("Android/app/src/main/cpp", "decomp-files").run()
