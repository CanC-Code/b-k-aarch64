#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.3 - Comprehensive Static/Forward-Decl Isolation Fix
Fixes over v75.2:
1. find_static_functions() regex now uses re.DOTALL so it correctly matches
   multi-line static function definitions (the v75.2 regex silently failed on
   functions whose return type and name spanned a newline).
2. find_forward_declared_functions() — new scanner that detects functions with
   an explicit non-static forward declaration (e.g. `void foo(Bar *x);`).
   These must also be excluded because the definition may be `static`, and the
   forward decl locks in a non-static implicit type that Clang rejects.
   This fixes: code_BF0.c — `void __codeBF0_draw(Actor *this);` on line 9
   followed by `static void __codeBF0_draw(Actor *this){` on line 20.
3. The combined exclusion set (static_funcs | forward_decl_funcs) is applied
   before any function is added to the BKA macro/alias list.
4. All other v75.1/v75.2 fixes retained.
"""

class SourceHarmonizerV753:
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
        print(f"[>] Preparing v75.3 Workspace...")
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
        """Removes strings and comments to provide a safe string for regex targeting."""
        text = re.sub(r'//[^\n]*', '', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)
        return text

    def find_static_functions(self, clean_content):
        """
        Pre-scan for all functions that are defined as 'static' anywhere in this file.
        Uses re.DOTALL so multiline return-type declarations are matched correctly.
        These must be excluded from BKA entirely — renaming their call sites causes
        Clang to generate an implicit non-static declaration that conflicts with the
        real static definition.
        """
        static_funcs = set()
        # Match: static ... func_name ( ... ) {
        # re.DOTALL allows [^;{}]* to cross newlines.
        static_def_pattern = re.compile(
            r'\bstatic\b[^;{}]*?\b([a-zA-Z_]\w*)\s*\([^{}]*?\)\s*\{',
            re.DOTALL
        )
        for match in static_def_pattern.finditer(clean_content):
            func_name = match.group(1)
            if func_name not in self.c_keywords:
                static_funcs.add(func_name)
        return static_funcs

    def find_forward_declared_functions(self, clean_content):
        """
        Pre-scan for all functions with an explicit non-static forward declaration,
        i.e. lines of the form:  <type> func_name(<params>);
        These must also be excluded because:
          - The forward decl establishes a non-static linkage for the name.
          - If the actual definition later uses 'static', Clang rejects it.
        This covers cases like code_BF0.c where `void __codeBF0_draw(Actor *this);`
        appears at the top of the file before `static void __codeBF0_draw(...){`.
        """
        forward_decl_funcs = set()
        # Match a declaration ending in ';' (not a definition ending in '{')
        # The name must not be preceded by 'static', 'extern', 'typedef' or 'inline'
        # on the same logical line segment.
        forward_decl_pattern = re.compile(
            r'(?<![;{}])\b([a-zA-Z_]\w*)\s*\([^{}]*?\)\s*;',
            re.DOTALL
        )
        for match in forward_decl_pattern.finditer(clean_content):
            func_name = match.group(1)
            if func_name in self.c_keywords:
                continue

            # Look at what precedes the match to determine if it's a non-static decl
            start = match.start()
            prefix = clean_content[:start]
            # Find the last statement boundary
            cut = max(prefix.rfind(';'), prefix.rfind('{'), prefix.rfind('}'))
            segment = prefix[cut+1:] if cut != -1 else prefix

            tokens = set(re.findall(r'[a-zA-Z_]\w*', segment))
            # Skip if it's a static/extern/inline/typedef declaration
            if tokens & {'static', 'extern', 'typedef', 'inline'}:
                continue
            # Must look like a type precedes the name — segment should have tokens
            # (avoids matching bare macro calls or control-flow calls)
            if not tokens:
                continue

            forward_decl_funcs.add(func_name)
        return forward_decl_funcs

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

        # --- v75.3: Build the full exclusion set before scanning for BKA candidates ---
        static_func_names   = self.find_static_functions(clean_content)
        forward_decl_names  = self.find_forward_declared_functions(clean_content)
        excluded_names      = static_func_names | forward_decl_names

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
            # Skip double-underscore internal/compiler-reserved names
            if func_name.startswith('__'):
                continue
            # Skip any function that is static or has a forward declaration in this file
            if func_name in excluded_names:
                continue

            # Context Filter: Look backwards to detect 'static', 'inline', 'typedef'
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
        print(f"[*] Applying v75.3 Function-Level Linker Isolation...")

        for file_path in self.target_dir.rglob('*.[ch]'):
            # Skip standard library headers and header files entirely
            if "include/libc" in str(file_path) or file_path.suffix == '.h': 
                continue
            
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception as e:
                print(f"[!] Error processing {file_path.name}: {e}")

        print(f"\n[+] v75.3 Complete.")
        print(f"    Files Processed: {self.stats['files_processed']}")
        print(f"    Files Modified:  {self.stats['changes_made']}")


if __name__ == "__main__":
    # Pointing to standard Banjo-Kazooie repository paths
    target = "Android/app/src/main/cpp"
    decomp = "decomp-files"
    
    harmonizer = SourceHarmonizerV753(target, decomp)
    harmonizer.run()
