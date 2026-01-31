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
                    with open(os.path.join(root, filename), 'r', errors='ignore') as f:
                        content = f.read()
                        for pat in patterns:
                            for match in re.findall(pat, content, re.DOTALL):
                                name = match[1] if match[1] else (match[2] if len(match)>2 else "")
                                if name and name not in self.symbol_db:
                                    self.symbol_db[name] = match[0]

    def rename_physical_headers(self):
        print("  [>] Clearing system header collisions...")
        for root, _, files in os.walk(self.root_path):
            for filename in files:
                if filename in self.renames:
                    old_path = os.path.join(root, filename)
                    new_path = os.path.join(root, self.renames[filename])
                    if not os.path.exists(new_path):
                        os.rename(old_path, new_path)

    def harmonize_file(self, path):
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
        
        orig = content
        # Sync Includes
        for old_h, new_h in self.renames.items():
            content = content.replace(f'<{old_h}>', f'"{new_h}"').replace(f'"{old_h}"', f'"{new_h}"')
        
        # Inject Types (Actor, Gfx, etc)
        is_core = any(x in content for x in ["ultra64.h", "gbi.h"])
        potential = set(re.findall(r'\b([sS][\w\d_]+|[a-zA-Z_][\w\d_]*_t|Bitmap|Gfx|ActorMarker|Actor)\b', content))
        
        needed = []
        if not is_core:
            for t in potential:
                if t in self.symbol_db and f"struct {t}" not in content:
                    needed.append(f"#ifndef _G_{t}\n#define _G_{t}\n{self.symbol_db[t]}\n#endif")

        if needed:
            content = "// --- HARMONIZER v4 ---\n" + "\n".join(needed) + "\n" + content

        if content != orig:
            with open(path, 'w') as f: f.write(content)
            return True
        return False

def prepare_source():
    android_cpp = "Android/app/src/main/cpp"
    if os.path.exists(android_cpp): shutil.rmtree(android_cpp)
    os.makedirs(android_cpp)
    shutil.copytree("decomp-files/include", os.path.join(android_cpp, "include"))
    shutil.copytree("decomp-files/src", os.path.join(android_cpp, "src"))

    harmonizer = SourceHarmonizer(android_cpp)
    harmonizer.rename_physical_headers()
    harmonizer.scan_symbols()
    
    count = 0
    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f.endswith(('.c', '.h')) and harmonizer.harmonize_file(os.path.join(root, f)):
                count += 1
    print(f"--- Finished: Patched {count} files ---")

if __name__ == "__main__":
    prepare_source()
