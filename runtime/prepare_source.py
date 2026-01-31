import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {} 
        # Maps problematic legacy headers to safe local names
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}

    def scan_symbols(self):
        print("  [>] Scanning project for all global types...")
        patterns = [
            r'((?:typedef\s+)?(?:struct|enum)\s*([\w\d_]*)\s*\{[^}]+\}\s*([\w\d_]*)\s*;)',
            r'(typedef\s+[\w\d_]+\s+([\w\d_]+)\s*;)',
            r'(struct\s+([\w\d_]+)\s*;)' 
        ]
        
        for root, _, files in os.walk(self.root_path):
            for filename in files:
                if filename.endswith(('.c', '.h')):
                    with open(os.path.join(root, filename), 'r', errors='ignore', encoding='utf-8') as f:
                        content = f.read()
                        for pat in patterns:
                            for match in re.findall(pat, content, re.DOTALL):
                                full_def = match[0]
                                name = match[1] if match[1] else (match[2] if len(match)>2 else "")
                                if name and name not in self.symbol_db:
                                    self.symbol_db[name] = full_def

    def rename_physical_headers(self):
        print("  [>] Renaming physical header files to avoid NDK collisions...")
        for root, _, files in os.walk(self.root_path):
            for filename in files:
                if filename in self.renames:
                    old_path = os.path.join(root, filename)
                    new_path = os.path.join(root, self.renames[filename])
                    if not os.path.exists(new_path):
                        os.rename(old_path, new_path)
                        print(f"      Renamed: {filename} -> {self.renames[filename]}")

    def harmonize_file(self, path):
        with open(path, 'r', errors='ignore', encoding='utf-8') as f:
            content = f.read()
        
        orig_content = content

        for old_h, new_h in self.renames.items():
            content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')
            content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')
        
        content = re.sub(r'#include\s+["<](?:2\.0L/PR/)?sched\.h[">]', '#include "game_sched.h"', content)

        is_core_header = any(x in content for x in ["ultra64.h", "gbi.h", "mbi.h"])
        potential_types = set(re.findall(r'\b([sS][\w\d_]+|[a-zA-Z_][\w\d_]*_t|audioInfo|Bitmap|Gfx|ActorMarker|Actor)\b', content))
        
        needed_defs = []
        if not is_core_header:
            for type_name in potential_types:
                if type_name in self.symbol_db and f"struct {type_name}" not in content:
                    guard = f"_GUARD_{type_name}"
                    needed_defs.append(f"#ifndef {guard}\n#define {guard}\n{self.symbol_db[type_name]}\n#endif")

        if needed_defs:
            injection = "\n// --- AUTOMATED HARMONIZER v3 ---\n" + "\n".join(needed_defs) + "\n"
            match = re.search(r'#include.*?\n', content)
            pos = match.end() if match else 0
            content = content[:pos] + injection + content[pos:]

        if content != orig_content:
            with open(path, 'w', encoding='utf-8') as f: f.write(content)
            return True
        return False

def prepare_source():
    print("--- Starting Automated Source Harmonization v3 ---")
    cpp_root = "Android/app/src/main/cpp"
    gen_src = os.path.join(cpp_root, "src")
    gen_inc = os.path.join(cpp_root, "include")
    
    # SAFE SYNC: Only wipe the target subdirectories, NOT the whole cpp folder
    for folder in [gen_src, gen_inc]:
        if os.path.exists(folder):
            print(f"  [!] Cleaning generated folder: {folder}")
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

    # Sync from decomp-files
    print("  [+] Syncing fresh files from decomp-files...")
    shutil.copytree("decomp-files/include", gen_inc, dirs_exist_ok=True)
    shutil.copytree("decomp-files/src", gen_src, dirs_exist_ok=True)

    harmonizer = SourceHarmonizer(cpp_root)
    harmonizer.rename_physical_headers()
    harmonizer.scan_symbols()
    
    count = 0
    for root, _, files in os.walk(cpp_root):
        for f in files:
            if f.endswith(('.c', '.h')):
                if harmonizer.harmonize_file(os.path.join(root, f)):
                    count += 1

    print(f"--- Finished: Patched {count} files ---")

if __name__ == "__main__":
    prepare_source()
