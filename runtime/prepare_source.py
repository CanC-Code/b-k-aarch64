import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {} 
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}

    def scan_symbols(self):
        print("  [>] Scanning for all global types and typedefs...")
        # Expanded pattern to catch Typedefs, Structs, and Enums even without names
        patterns = [
            r'((?:typedef\s+)?(?:struct|enum)\s*([\w\d_]*)\s*\{[^}]+\}\s*([\w\d_]*)\s*;)',
            r'(typedef\s+[\w\d_]+\s+([\w\d_]+)\s*;)' # Catch simple typedefs like 'typedef int Bitmap;'
        ]
        
        for root, _, files in os.walk(self.root_path):
            for filename in files:
                if filename.endswith(('.c', '.h')):
                    with open(os.path.join(root, filename), 'r', errors='ignore') as f:
                        content = f.read()
                        for pat in patterns:
                            matches = re.findall(pat, content, re.DOTALL)
                            for match in matches:
                                full_def = match[0]
                                name = match[1] if match[1] else (match[2] if len(match)>2 else "")
                                if name and name not in self.symbol_db:
                                    self.symbol_db[name] = full_def

    def harmonize_file(self, path, filename):
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
        
        orig_content = content

        # A. Header & Array Fixes
        for old_h, new_h in self.renames.items():
            content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')
            content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')
        
        content = re.sub(r'#include\s+["<](?:2\.0L/PR/)?sched\.h[">]', '#include "game_sched.h"', content)
        content = re.sub(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);', 
                         r'\1 \2[\3]; memcpy(\2, \4, \3); // [PATCHED]', content)

        # B. Dependency Injection with Collision Prevention
        # We only inject if the primary headers (ultra64.h, gbi.h) are NOT present 
        # to avoid the "redefinition" errors seen in the log.
        is_core_header_present = any(x in content for x in ["ultra64.h", "gbi.h", "mbi.h"])
        
        potential_types = set(re.findall(r'\b([sS][\w\d_]+|[a-zA-Z_][\w\d_]*_t|audioInfo|Bitmap|Gfx)\b', content))
        needed_defs = []

        if not is_core_header_present:
            for type_name in potential_types:
                if type_name in self.symbol_db and f" {type_name}" not in content:
                    guard = f"_GUARD_{type_name}"
                    needed_defs.append(f"#ifndef {guard}\n#define {guard}\n{self.symbol_db[type_name]}\n#endif")

        # C. Linkage Harmonizer
        static_funcs = re.findall(r'^static\s+[\w\*]+\s+([\w\d_]+)\s*\(', content, re.MULTILINE)
        prototypes = [f"{re.search(r'^(static\s+[\w\*]+\s+' + re.escape(f) + r'\s*\([^)]*\))', content, re.MULTILINE).group(1)};" 
                      for f in static_funcs if re.search(r'^(static\s+[\w\*]+\s+' + re.escape(f) + r'\s*\([^)]*\))', content, re.MULTILINE)]

        # D. Inject at top
        if needed_defs or prototypes:
            injection = "\n// --- AUTOMATED HARMONIZER BLOCK ---\n"
            injection += "\n".join(needed_defs) + "\n"
            injection += "\n".join(prototypes) + "\n"
            
            # Find first include or first line to inject
            insert_pos = 0
            include_match = re.search(r'#include.*?\n', content)
            if include_match:
                insert_pos = include_match.end()
            content = content[:insert_pos] + injection + content[insert_pos:]

        # E. Specific Core Fixes
        if filename == "code_1D00.c":
            content = content.replace('extern void n_alInit(N_ALGlobals *, ALSynConfig *);', '// [PATCHED]')

        if content != orig_content:
            with open(path, 'w') as f: f.write(content)
            return True
        return False

def prepare_source():
    print("--- Starting Automated Source Harmonization v2 ---")
    src_root, android_cpp_path = "decomp-files", "Android/app/src/main/cpp"
    
    for sub in ["include", "src"]:
        full_src, full_dest = os.path.join(src_root, sub), os.path.join(android_cpp_path, sub)
        if os.path.exists(full_src):
            if os.path.exists(full_dest): shutil.rmtree(full_dest)
            shutil.copytree(full_src, full_dest)

    harmonizer = SourceHarmonizer(android_cpp_path)
    harmonizer.scan_symbols()
    
    patched_count = sum(1 for root, _, files in os.walk(android_cpp_path) 
                        for f in files if f.endswith(('.c', '.h')) and harmonizer.harmonize_file(os.path.join(root, f), f))

    print(f"--- Finished: Patched {patched_count} files ---")

if __name__ == "__main__":
    prepare_source()
