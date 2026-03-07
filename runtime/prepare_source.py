#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.1 - Zero-Header Linker Isolation (Refined)
Fixes:
1. Drops 'harmonized_globals.h' entirely, eliminating all "Incomplete Type" and "Conflicting Type" errors.
2. Uses Weak Alias export strategy to perfectly mimic N64 overlay isolation on AArch64.
3. Protects entrypoint 'main_no_args' from being aliased so NativeBridge.cpp can link it.
4. Replaces invalid array assignments (u8 tmp[6] = D_...) with __builtin_memcpy to satisfy Clang.
"""

class SourceHarmonizerV75:
    def __init__(self, target_dir, decomp_path):
        self.target_dir = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0}
        
        # Standard C keywords to ignore
        self.c_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do', 
            'break', 'continue', 'case', 'default', 'goto', 'struct', 'union', 
            'enum', 'static', 'extern', 'const', 'volatile', 'inline', 'typedef'
        }
        
        # Standard lib functions and crucial JNI/C++ entrypoints to ignore
        self.std_c = {
            'main', 'main_no_args', 'memcpy', 'memset', 'strlen', 'strcpy', 'strcmp', 
            'sprintf', 'printf', 'malloc', 'free', 'sin', 'cos', 'sinf', 
            'cosf', 'sqrt', 'sqrtf', 'abs', 'fabs'
        }
        
        # SDK & internal low-level prefixes that must remain linked globally
        self.sdk_prefixes = ('os', 'gu', 'al', 'gS', 'gD', 'gd', '__os', 'sp', 'dp', 'rmon')

    def setup_workspace(self):
        print(f"[>] Preparing v75.1 Workspace...")
        src_target = self.target_dir / "src"
        include_target = self.target_dir / "include"
        
        for folder in [src_target, include_target]:
            if folder.exists():
                shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
            
        for sub in ["src", "include"]:
            src = self.decomp_path / sub
            dst = self.target_dir / sub
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)

    def remove_strings_and_comments(self, text):
        """Removes strings and comments to provide a safe string for Regex targeting."""
        text = re.sub(r'//.*', '', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'".*?"', '""', text, flags=re.DOTALL)
        return text

    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()

        # Fix IDO-specific array assignment (Clang rejects `u8 tmp[6] = D_80390DA0;`)
        array_init_pattern = re.compile(
            r'^([ \t]*(?:struct\s+|union\s+|enum\s+)?[a-zA-Z_]\w*(?:\s*\*)*)\s+([a-zA-Z_]\w*)\s*\[\s*(\d+)\s*\]\s*=\s*([a-zA-Z_]\w*)\s*;',
            re.MULTILINE
        )
        
        def array_init_repl(match):
            type_str = match.group(1)
            name = match.group(2)
            size = match.group(3)
            src = match.group(4)
            clean_type = type_str.strip()
            return f"{type_str} {name}[{size}]; __builtin_memcpy({name}, {src}, {size} * sizeof({clean_type}));"
        
        modified_content = array_init_pattern.sub(array_init_repl, original_content)
        clean_content = self.remove_strings_and_comments(modified_content)
        
        fid = hashlib.md5(str(file_path.name).encode()).hexdigest()[:8]
        
        # Matches: func_name(...) { 
        func_pattern = re.compile(r'\b([a-zA-Z_]\w*)\s*\([^{;]*\)\s*\{')
        
        defined_funcs = []
        for match in func_pattern.finditer(clean_content):
            func_name = match.group(1)
            start_idx = match.start()
            
            # Exclusion Filters
            if func_name in self.c_keywords or func_name in self.std_c:
                continue
            if func_name.startswith(self.sdk_prefixes):
                continue
            if func_name.isupper():
                continue

            # Context Filter: Look backwards to the previous statement to detect 'static', 'inline' or 'typedef'
            prefix_str = clean_content[:start_idx]
            cut_idx = max(prefix_str.rfind(';'), prefix_str.rfind('}'), prefix_str.rfind('{'))
            if cut_idx != -1:
                prefix_str = prefix_str[cut_idx+1:]
            
            tokens = re.findall(r'[a-zA-Z_]\w*', prefix_str)
            if any(k in tokens for k in ['static', 'inline', 'typedef']):
                continue
                
            defined_funcs.append(func_name)

        # Deduplicate while preserving order
        defined_funcs = list(dict.fromkeys(defined_funcs))

        # Prepare Injection Blocks
        macros = ""
        aliases = ""
        
        if defined_funcs:
            macros += "// --- BKA MACROS START ---\n"
            aliases += "\n\n// --- BKA ALIASES START ---\n"
            
            for func in defined_funcs:
                unique_name = f"BKA_F_{fid}_{func}"
                
                # The macro silently renames the definition and local calls
                macros += f"#define {func} {unique_name}\n"
                
                # The weak alias securely exposes the symbol for cross-file linking
                aliases += f"#undef {func}\n"
                aliases += f"__typeof__({unique_name}) {func} __attribute__((weak, alias(\"{unique_name}\")));\n"

            macros += "// --- BKA MACROS END ---\n\n"
            aliases += "// --- BKA ALIASES END ---\n"

        # Reconstruct the file with macros at the absolute top, aliases at the absolute bottom
        new_content = macros + modified_content + aliases

        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            self.stats["changes_made"] += 1

    def run(self):
        if not self.decomp_path.exists():
            print(f"[!] Error: Decompilation path {self.decomp_path} not found.")
            return

        self.setup_workspace()
        print(f"[*] Applying v75.1 Function-Level Linker Isolation...")

        for file_path in self.target_dir.rglob('*.[ch]'):
            # Skip standard library headers and header files entirely
            if "include/libc" in str(file_path) or file_path.suffix == '.h': 
                continue
            
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")

        print(f"\n[+] v75.1 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    # Pointing to standard Banjo-Kazooie repository paths
    target = "Android/app/src/main/cpp"
    decomp = "decomp-files"
    
    harmonizer = SourceHarmonizerV75(target, decomp)
    harmonizer.run()
