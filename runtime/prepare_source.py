import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {}
        # Maps system headers to game-specific headers to avoid NDK collisions
        self.renames = {
            "string.h": "game_string.h",
            "time.h": "game_time.h",
            "sched.h": "game_sched.h"
        }

    def scan_symbols(self):
        print("  [>] Scanning for global types and structs...")
        # Patterns to find typedefs and struct definitions in the decomp files
        patterns = [
            r'((?:typedef\s+)?(?:struct|enum)\s*([\w\d_]*)\s*\{[^}]+\}\s*([\w\d_]*)\s*;)',
            r'(typedef\s+[\w\d_]+\s+([\w\d_]+)\s*;)',
            r'(struct\s+([\w\d_]+)\s*;)'
        ]
        for root, _, files in os.walk(self.root_path):
            for filename in files:
                if filename.endswith(('.c', '.h')):
                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            for pat in patterns:
                                for match in re.findall(pat, content, re.DOTALL):
                                    name = match[1] if match[1] else (match[2] if len(match) > 2 else "")
                                    if name and name not in self.symbol_db:
                                        self.symbol_db[name] = match[0]
                    except Exception as e:
                        print(f"      [!] Error scanning {filename}: {e}")

    def rename_physical_headers(self):
        print("  [>] Renaming colliding headers...")
        for root, _, files in os.walk(self.root_path):
            for filename in files:
                if filename in self.renames:
                    old_path = os.path.join(root, filename)
                    new_path = os.path.join(root, self.renames[filename])
                    if not os.path.exists(new_path):
                        os.rename(old_path, new_path)

    def harmonize_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            orig = content
            # Update include statements to point to renamed headers
            for old_h, new_h in self.renames.items():
                content = content.replace(f'<{old_h}>', f'"{new_h}"').replace(f'"{old_h}"', f'"{new_h}"')
            
            # Identify required symbols for the file
            is_core = any(x in content for x in ["ultra64.h", "gbi.h"])
            potential = set(re.findall(r'\b([sS][\w\d_]+|[a-zA-Z_][\w\d_]*_t|Bitmap|Gfx|ActorMarker|Actor)\b', content))
            
            needed = []
            if not is_core:
                for t in potential:
                    if t in self.symbol_db and f"struct {t}" not in content:
                        # Prevent duplicate injection
                        if f"#ifndef _G_{t}" not in content:
                            needed.append(f"#ifndef _G_{t}\n#define _G_{t}\n{self.symbol_db[t]}\n#endif")

            if needed:
                content = "// --- HARMONIZED ---\n" + "\n".join(needed) + "\n" + content

            if content != orig:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
        except Exception as e:
            print(f"      [!] Error harmonizing {os.path.basename(path)}: {e}")
        return False

def prepare_source():
    print("--- Starting Selective Harmonization v5 ---")
    
    # Project Paths
    cpp_root = "Android/app/src/main/cpp"
    gen_src = os.path.join(cpp_root, "src")
    gen_inc = os.path.join(cpp_root, "include")
    
    # Check if decomp sources exist
    if not os.path.exists("decomp-files"):
        print("  [!] Error: 'decomp-files' directory not found!")
        return

    # 1. Selective Wipe: Clean subdirectories but PROTECT root files (NativeBridge.cpp, etc.)
    for folder in [gen_src, gen_inc]:
        if os.path.exists(folder):
            print(f"  [!] Cleaning generated folder: {folder}")
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

    # 2. Sync: Copy fresh files into the structure
    print("  [>] Syncing fresh source and headers...")
    shutil.copytree("decomp-files/src", gen_src, dirs_exist_ok=True)
    shutil.copytree("decomp-files/include", gen_inc, dirs_exist_ok=True)

    # 3. Process: Harmonize everything within the cpp_root
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
