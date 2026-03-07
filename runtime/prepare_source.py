#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import shutil
from pathlib import Path

"""
SourceHarmonizer v75.10 — Comprehensive C89/IDO-to-Clang Source Normalisation

FEATURES:
1. Zero-Header Linker Isolation: Uses Weak Alias strategy to allow duplicate static names.
2. Clang-Strict Array Initialisation: Replaces 'u8 arr[N] = D_ADDR' with __builtin_memcpy.
3. C89 Logic Repair: Fixes illegal 'static var = func()' assignments.
4. Substring Collision Prevention: Sorts symbols by length descending.
5. Alias Visibility: Injects 'extern' forward declarations for BKA unique names.
"""

class SourceHarmonizer:
    def __init__(self, target_dir, decomp_path):
        self.target_dir = Path(target_dir)
        self.decomp_path = Path(decomp_path)
        self.stats = {"files_processed": 0, "changes_made": 0}
        
        self.c_keywords = {
            'if', 'while', 'for', 'switch', 'return', 'sizeof', 'else', 'do', 
            'break', 'continue', 'case', 'default', 'goto', 'struct', 'union', 
            'enum', 'static', 'extern', 'const', 'volatile', 'inline', 'typedef'
        }
        self.protected_symbols = {
            'main', 'main_no_args', 'memcpy', 'memset', 'strlen', 'strcpy', 'strcmp', 
            'sprintf', 'printf', 'malloc', 'free', 'sin', 'cos', 'sinf', 'cosf', 
            'sqrt', 'sqrtf', 'abs', 'fabs'
        }
        self.sdk_prefixes = ('os', 'gu', 'al', 'gS', 'gD', 'gd', '__os', 'sp', 'dp', 'rmon')

    def setup_workspace(self):
        src_target = self.target_dir / "src"
        include_target = self.target_dir / "include"
        for folder in [src_target, include_target]:
            if folder.exists(): shutil.rmtree(folder)
            folder.mkdir(parents=True, exist_ok=True)
        
        for sub in ["src", "include"]:
            src = self.decomp_path / sub
            dst = self.target_dir / sub
            if src.exists(): shutil.copytree(src, dst, dirs_exist_ok=True)

    def strip_garbage(self, text):
        text = re.sub(r'//.*', '', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        text = re.sub(r'".*?"', '""', text, flags=re.DOTALL)
        return text

    def apply_c89_static_fixes(self, content):
        lines = content.splitlines()
        new_lines = []
        for line in lines:
            match = re.match(r'^(\s*)static\s+([a-zA-Z_]\w*(?:\s+\*+)?\s+)?([a-zA-Z_]\w*(?:(?:->|\.)\w+)?(?:\[[^\]]+\])?)\s*=\s*([^;]+);(.*)$', line)
            if match:
                indent, type_part, target, value, trailing = match.groups()
                if '(' in value:
                    if type_part:
                        new_lines.append(f"{indent}static {type_part}{target};")
                        new_lines.append(f"{indent}{target} = {value};{trailing}")
                    else:
                        new_lines.append(f"{indent}{target} = {value};{trailing}")
                    continue
            new_lines.append(line)
        return "\n".join(new_lines)

    def process_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        fid = hashlib.md5(str(file_path.name).encode()).hexdigest()[:8]

        # 1. Array Initialization Fix
        array_pattern = re.compile(
            r'^([ \t]*(?:struct\s+|union\s+|enum\s+)?[a-zA-Z_]\w*(?:\s*\*)*)\s+([a-zA-Z_]\w*)\s*\[\s*(\d+)\s*\]\s*=\s*([a-zA-Z_]\w*)\s*;',
            re.MULTILINE
        )
        content = array_pattern.sub(
            lambda m: f"{m.group(1)} {m.group(2)}[{m.group(3)}]; __builtin_memcpy({m.group(2)}, {m.group(4)}, {m.group(3)} * sizeof({m.group(1).strip()}));", 
            content
        )

        # 2. C89 Static Assignment Fix
        content = self.apply_c89_static_fixes(content)

        # 3. Static Function Scoping
        clean_content = self.strip_garbage(content)
        func_pattern = re.compile(r'\b([a-zA-Z_]\w*)\s*\([^{;]*\)\s*\{')
        found_statics = []
        for match in func_pattern.finditer(clean_content):
            name = match.group(1)
            if name in self.c_keywords or name in self.protected_symbols or name.startswith(self.sdk_prefixes):
                continue
            
            pre_context = clean_content[:match.start()]
            last_break = max(pre_context.rfind(';'), pre_context.rfind('}'), pre_context.rfind('{'))
            if 'static' in pre_context[last_break+1:]:
                found_statics.append(name)

        # 4. Symbol Replacement (Sorted by length DESC to avoid partial name bugs)
        found_statics = sorted(list(set(found_statics)), key=len, reverse=True)
        replacements = {fn: f"BKA_F_{fid}_{fn}" for fn in found_statics}
        for fn, un in replacements.items():
            content = re.sub(rf'\b{fn}\b', un, content)

        # 5. Alias and Forward-Declaration Injection
        if replacements:
            macros = "// --- BKA MACROS START ---\n"
            aliases = "\n// --- BKA ALIASES START ---\n"
            for fn, un in replacements.items():
                macros += f"extern __typeof__({un}) {un};\n"
                aliases += f"__typeof__({un}) {fn} __attribute__((weak, alias(\"{un}\")));\n"
            macros += "// --- BKA MACROS END ---\n\n"
            aliases += "// --- BKA ALIASES END ---\n"
            content = macros + content + aliases

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.stats["changes_made"] += 1

    def run(self):
        self.setup_workspace()
        for file_path in (self.target_dir / "src").rglob('*.[ch]'):
            if "include/libc" in str(file_path) or file_path.suffix == '.h':
                continue
            try:
                self.process_file(file_path)
                self.stats["files_processed"] += 1
            except Exception:
                pass

if __name__ == "__main__":
    harmonizer = SourceHarmonizer("Android/app/src/main/cpp", "decomp-files")
    harmonizer.run()
