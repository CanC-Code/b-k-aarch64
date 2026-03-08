#!/usr/bin/env python3
import os
import re
import sys
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.25 — Architectural Type & Linkage Sync

═══════════════════════════════════════════════════════════════════════════════
LOG 49 — Pass 6 Array Validation successful. New Architectural Conflict:
  memory.c: conflicting types for '__osMalloc' (u32 vs s32, void* vs OSHeapHandle*)
═══════════════════════════════════════════════════════════════════════════════

KEY UPGRADES in v75.25:
  1. Pass 7 (Signature Coercion): Dynamically rewrites function implementations 
     to match SDK prototypes, specifically targeting OS/SDK symbol collisions.
  2. Recursive Typedef Injection: Injects N64-standard types (u32, s32, f32) into
     the global header chain to prevent "unknown type" errors in complex includes.
  3. Pointer Transparency: Handles the OSHeapHandle vs void* abstraction.
"""

class SourceHarmonizerV7525:
    def __init__(self, target_dir, decomp_path):
        self.target_dir  = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0, "coercions": 0}
        self.sdk_truth = {} # {func_name: (full_prototype, return_type)}

        self.c_keywords = {'if','while','for','switch','return','sizeof','else','do','break','continue','case','default','goto','struct','union','enum','static','extern','const','volatile','inline','typedef'}
        self._ctrl_keywords = {'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do', 'break', 'continue', 'case', 'default', 'goto', 'typedef'}

    def setup_workspace(self):
        print(f"[>] Synchronizing Architecture: {self.target_dir}")
        for folder in [self.target_dir / "src", self.target_dir / "include"]:
            if folder.exists(): shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
        for sub in ["src", "include"]:
            src = self.decomp_path / sub
            dst = self.target_dir / sub
            if src.exists(): shutil.copytree(src, dst, dirs_exist_ok=True)

    def patch_global_headers(self):
        """Pass 0: Deep Type Injection"""
        # Inject standard N64 types into ultra-low-level headers
        types_block = (
            "\n// SH v75.25 Global Type Guard\n"
            "#ifndef _SH_TYPES_H\n#define _SH_TYPES_H\n"
            "typedef signed char            s8;\n"
            "typedef unsigned char          u8;\n"
            "typedef signed short           s16;\n"
            "typedef unsigned short         u16;\n"
            "typedef signed int             s32;\n"
            "typedef unsigned int           u32;\n"
            "typedef signed long long       s64;\n"
            "typedef unsigned long long     u64;\n"
            "typedef float                  f32;\n"
            "typedef double                 f64;\n"
            "#endif\n"
        )
        
        # Target the main SDK header for truth extraction and type safety
        os_h = self.target_dir / "include" / "2.0L" / "PR" / "os.h"
        if os_h.exists():
            content = os_h.read_text(encoding='utf-8', errors='ignore')
            os_h.write_text(types_block + content)

    def scan_sdk_for_truth(self):
        """Pass 7a: Cataloging the OS/SDK prototypes we MUST match"""
        print("[>] Cataloging SDK Linkage Truth...")
        # Matches: extern [ReturnType] [FuncName]([Params]);
        sdk_pat = re.compile(r'extern\s+([a-zA-Z0-9_\s\*]+?)\b([a-zA-Z_]\w*)\s*\(([^;]*)\)\s*;', re.MULTILINE)
        for h_file in self.target_dir.rglob('*.h'):
            content = re.sub(r'/\*.*?\*/|//[^\n]*', '', h_file.read_text(encoding='utf-8', errors='ignore'), flags=re.DOTALL)
            for m in sdk_pat.finditer(content):
                rtype, name, params = m.group(1).strip(), m.group(2), m.group(3).strip()
                if name.startswith('os') or name.startswith('__os') or name.startswith('gu'):
                    self.sdk_truth[name] = (rtype, params)

    def coerce_signatures(self, content):
        """Pass 7b: Implementation Force-Alignment"""
        modified = content
        for name, (rtype, params) in self.sdk_truth.items():
            # Pattern: [AnyType] name([AnyParams]) {
            impl_pat = re.compile(r'^([a-zA-Z0-9_\s\*]+?)\b' + re.escape(name) + r'\s*\(([^)]*)\)\s*\{', re.MULTILINE)
            
            def _apply_coercion(m):
                curr_rtype = m.group(1).strip()
                curr_params = m.group(2).strip()
                
                # Check if we actually need to change it
                if curr_rtype == rtype and curr_params == params:
                    return m.group(0)
                
                self.stats["coercions"] += 1
                # Enforce the SDK prototype while keeping the opening brace
                return f"{rtype} {name}({params}) {{"

            modified = impl_pat.sub(_apply_coercion, modified)
        return modified

    def validate_array_initializers(self, content):
        """Pass 6: Alignment/Syntax Verification (from v75.24)"""
        illegal_init_pat = re.compile(
            r'^([ \t]*(?:struct\s+|union\s+|enum\s+)?[a-zA-Z_]\w*(?:\s*\*)*)\s+'
            r'([a-zA-Z_]\w*)\s*\[\s*(\d+|[A-Z_0-9]+)\s*\]\s*=\s*'
            r'([a-zA-Z_]\w*)\s*;', re.MULTILINE
        )
        def _fix(m):
            t, n, s, v = m.group(1), m.group(2), m.group(3), m.group(4)
            if v.isdigit() or v.isupper(): return m.group(0) 
            return f"{t} {n}[{s}];\n    __builtin_memcpy({n}, {v}, {s} * sizeof({t.strip()}));"
        return illegal_init_pat.sub(_fix, content)

    def process_file(self, file_path):
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        original = content
        
        # Pipeline: Array Validation -> Linkage Coercion
        content = self.validate_array_initializers(content)
        content = self.coerce_signatures(content)
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            self.stats["changes_made"] += 1

    def run(self):
        self.setup_workspace()
        self.patch_global_headers()
        self.scan_sdk_for_truth()
        
        for file_path in self.target_dir.rglob('*.c'):
            if "include/libc" not in str(file_path):
                self.process_file(file_path)
                self.stats["files_processed"] += 1
                
        print(f"\n[+] v75.25 Architectural Sync Complete.")
        print(f"    - Functions Coerced to SDK Truth: {self.stats['coercions']}")
        print(f"    - Files Successfully Harmonized: {self.stats['changes_made']}")

if __name__ == "__main__":
    SourceHarmonizerV7525("Android/app/src/main/cpp", "decomp-files").run()
