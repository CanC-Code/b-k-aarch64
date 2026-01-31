import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {} 
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}

    def scan_symbols(self):
        print("  [>] Scanning for global types...")
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
                                name = match[1] if match[1] else (match[2] if len(match)>2 else "")
                                if name and name not in self.symbol_db:
                                    self.symbol_db[name] = match[0]

    def rename_physical_headers(self):
        for root, _, files in os.walk(self.root_path):
            for filename in files:
                if filename in self.renames:
                    old_path = os.path.join(root, filename)
                    new_path = os.path.join(root, self.renames[filename])
                    if not os.path.exists(new_path):
                        os.rename(old_path, new_path)

    def harmonize_file(self, path):
        with open(path, 'r', errors='ignore', encoding='utf-8') as f:
            content = f.read()
        orig = content
        for old, new in self.renames.items():
            content = content.replace(f'#include <{old}>', f'#include "{new}"')
            content = content.replace(f'#include "{old}"', f'#include "{new}"')
        
        # Inject guards for types found during scan
        is_core = any(x in content for x in ["ultra64.h", "gbi.h", "mbi.h"])
        types = set(re.findall(r'\b([sS][\w\d_]+|[a-zA-Z_][\w\d_]*_t|audioInfo|Bitmap|Gfx|ActorMarker|Actor)\b', content))
        
        needed = []
        if not is_core:
            for t in types:
                if t in self.symbol_db and f"struct {t}" not in content:
                    needed.append(f"#ifndef _G_{t}\n#define _G_{t}\n{self.symbol_db[t]}\n#endif")

        if needed:
            content = "// --- HARMONIZED ---\n" + "\n".join(needed) + "\n" + content
        if content != orig:
            with open(path, 'w', encoding='utf-8') as f: f.write(content)
            return True
        return False

def prepare_source():
    cpp_root = "Android/app/src/main/cpp"
    # CRITICAL: Selective wipe to prevent redefinition while protecting build files
    for sub in ["src", "include"]:
        target = os.path.join(cpp_root, sub)
        if os.path.exists(target): shutil.rmtree(target)
        os.makedirs(target)

    shutil.copytree("decomp-files/include", os.path.join(cpp_root, "include"), dirs_exist_ok=True)
    shutil.copytree("decomp-files/src", os.path.join(cpp_root, "src"), dirs_exist_ok=True)

    h = SourceHarmonizer(cpp_root)
    h.rename_physical_headers()
    h.scan_symbols()
    [h.harmonize_file(os.path.join(r, f)) for r, _, fs in os.walk(cpp_root) for f in fs if f.endswith(('.c', '.h'))]

if __name__ == "__main__":
    prepare_source()
