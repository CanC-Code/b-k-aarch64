import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {}
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
        # NEW: Blacklist symbols that are causing redefinition loops
        self.blacklist = ["sprite", "sfx_e", "OSMesg", "OSThread", "OSTask"]

    def scan_symbols(self):
        print("  [>] Brute-force scanning project...")
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
                                full_def = match[0]
                                name = match[1] if match[1] else (match[2] if len(match)>2 else "")
                                if name and name not in self.symbol_db and name not in self.blacklist:
                                    self.symbol_db[name] = full_def

    def rename_physical_headers(self):
        for root, _, files in os.walk(self.root_path):
            for filename in files:
                if filename in self.renames:
                    old_path = os.path.join(root, filename)
                    new_path = os.path.join(root, self.renames[filename])
                    if not os.path.exists(new_path): os.rename(old_path, new_path)

    def harmonize_file(self, path, filename):
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
        orig_content = content

        for old_h, new_h in self.renames.items():
            content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')
            content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

        # Core headers are "untouchable" - we don't inject into them
        is_core = any(x in filename for x in ["ultra64.h", "gbi.h", "mbi.h", "sptask.h", "enums.h", "functions.h"])
        
        if not is_core:
            # 1. Dependency Injection (Strict check)
            potential_types = set(re.findall(r'\b([sS][\w\d_]+|[a-zA-Z_][\w\d_]*_t|ActorMarker|Gfx|BK[\w\d_]+)\b', content))
            needed_defs = []
            for type_name in potential_types:
                # ONLY inject if it's NOT in the blacklist and NOT already present
                if type_name in self.symbol_db and type_name not in self.blacklist:
                    if f"struct {type_name}" not in content and f"enum {type_name}" not in content:
                        guard = f"_GUARD_{type_name}"
                        needed_defs.append(f"#ifndef {guard}\n#define {guard}\n{self.symbol_db[type_name]}\n#endif")
            
            # 2. Static Prototype Generation
            static_funcs = re.findall(r'^static\s+[\w\*]+\s+([\w\d_]+)\s*\(', content, re.MULTILINE)
            prototypes = [f"{re.search(r'^(static\s+[\w\*]+\s+' + re.escape(f) + r'\s*\([^)]*\))', content, re.MULTILINE).group(1)};" 
                          for f in static_funcs if re.search(r'^(static\s+[\w\*]+\s+' + re.escape(f) + r'\s*\([^)]*\))', content, re.MULTILINE)]

            if needed_defs or prototypes:
                injection = "\n// --- HARMONIZER v3.9 ---\n" + "\n".join(needed_defs + prototypes) + "\n"
                match = re.search(r'#include.*?\n', content)
                pos = match.end() if match else 0
                content = content[:pos] + injection + content[pos:]

        if content != orig_content:
            with open(path, 'w') as f: f.write(content)
            return True
        return False

def prepare_source():
    android_cpp = "Android/app/src/main/cpp"
    for sub in ["src", "include"]:
        target = os.path.join(android_cpp, sub)
        if os.path.exists(target): shutil.rmtree(target)
        os.makedirs(target, exist_ok=True)

    shutil.copytree("decomp-files/include", os.path.join(android_cpp, "include"), dirs_exist_ok=True)
    shutil.copytree("decomp-files/src", os.path.join(android_cpp, "src"), dirs_exist_ok=True)

    harmonizer = SourceHarmonizer(android_cpp)
    harmonizer.rename_physical_headers()
    harmonizer.scan_symbols()

    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f.endswith(('.c', '.h')):
                harmonizer.harmonize_file(os.path.join(root, f), f)

if __name__ == "__main__":
    prepare_source()
