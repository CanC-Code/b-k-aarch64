import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {}  # { 'struct_name': 'full_definition_text' }
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}

    def scan_symbols(self):
        print("  [>] Scanning project for global types...")
        # Regex to capture structs, enums, and typedefs across the whole project
        type_pattern = r'((?:typedef\s+)?(?:struct|enum)\s*([\w\d_]*)\s*\{[^}]+\}\s*([\w\d_]*)\s*;)'
        
        for root, _, files in os.walk(self.root_path):
            for filename in files:
                if filename.endswith(('.c', '.h')):
                    with open(os.path.join(root, filename), 'r', errors='ignore') as f:
                        content = f.read()
                        matches = re.findall(type_pattern, content, re.DOTALL)
                        for full_def, name1, name2 in matches:
                            name = name1 if name1 else name2
                            if name and name not in self.symbol_db:
                                self.symbol_db[name] = full_def

    def harmonize_file(self, path, filename):
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
        
        orig_content = content

        # A. Header Normalization
        for old_h, new_h in self.renames.items():
            content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')
            content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')
        content = re.sub(r'#include\s+["<](?:2\.0L/PR/)?sched\.h[">]', '#include "game_sched.h"', content)

        # B. Legacy Array Fix (Standardizes non-compliant N64 assignments)
        content = re.sub(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);', 
                         r'\1 \2[\3]; memcpy(\2, \4, \3); // [PATCHED]', content)

        # C. Automated Dependency Injection (The "Linker" Logic)
        # Finds words that look like types (sStructName) used in the code
        potential_types = set(re.findall(r'\b([sS][\w\d_]+|[a-zA-Z_][\w\d_]*_t|audioInfo)\b', content))
        
        needed_defs = []
        for type_name in potential_types:
            if type_name in self.symbol_db and f"struct {type_name}" not in content and f"typedef struct {type_name}" not in content:
                # Wrap in guards to prevent redefinition errors
                guard = f"_GUARD_{type_name}"
                guarded_def = f"#ifndef {guard}\n#define {guard}\n{self.symbol_db[type_name]}\n#endif"
                needed_defs.append(guarded_def)

        # D. Linkage Harmonizer (Static vs Extern)
        static_funcs = re.findall(r'^static\s+[\w\*]+\s+([\w\d_]+)\s*\(', content, re.MULTILINE)
        prototypes = []
        for func in static_funcs:
            # Create forward declarations for all static functions to solve top-down visibility
            sig_match = re.search(r'^(static\s+[\w\*]+\s+' + re.escape(func) + r'\s*\([^)]*\))', content, re.MULTILINE)
            if sig_match:
                prototypes.append(f"{sig_match.group(1)};")
            # Fix conflicting non-static declarations
            content = re.sub(r'^([\w\*]+\s+' + re.escape(func) + r'\s*\([^;]*\);)', r'static \1', content, flags=re.MULTILINE)

        # Injection: Place all discovered types and prototypes at the top
        if needed_defs or prototypes:
            injection = "\n// --- AUTOMATED HARMONIZER BLOCK ---\n"
            injection += "\n".join(needed_defs) + "\n"
            injection += "\n".join(prototypes) + "\n"
            
            include_matches = list(re.finditer(r'#include.*?\n', content))
            insert_pos = include_matches[-1].end() if include_matches else 0
            content = content[:insert_pos] + injection + content[insert_pos:]

        # E. Specific Core Fixes (Remaining edge cases)
        if filename == "code_1D00.c":
            content = content.replace('extern void n_alInit(N_ALGlobals *, ALSynConfig *);', '// [PATCHED]')
            if 'D_8027D5B0' in content and 'extern struct' not in content:
                content += "\nextern struct { int unk0; int unk4; struct audioInfo* unk8; } D_8027D5B0;\n"

        if content != orig_content:
            with open(path, 'w') as f: f.write(content)
            return True
        return False

def prepare_source():
    print("--- Starting Automated Source Harmonization ---")
    src_root = "decomp-files"
    android_cpp_path = "Android/app/src/main/cpp"
    
    # 1. Sync Files
    for sub in ["include", "src"]:
        full_src, full_dest = os.path.join(src_root, sub), os.path.join(android_cpp_path, sub)
        if os.path.exists(full_src):
            if os.path.exists(full_dest): shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)

    # 2. Run Harmonizer
    harmonizer = SourceHarmonizer(android_cpp_path)
    harmonizer.scan_symbols()
    
    patched_count = 0
    for root, _, files in os.walk(android_cpp_path):
        for filename in files:
            if filename.endswith(('.c', '.cpp', '.h')):
                if harmonizer.harmonize_file(os.path.join(root, filename), filename):
                    patched_count += 1

    print(f"--- Finished: Patched {patched_count} files ---")

if __name__ == "__main__":
    prepare_source()
