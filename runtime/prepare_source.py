import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {}
        # Core renames for Android NDK system compatibility
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}

    def enforce_header_guards(self, path, filename):
        """Prevents the 'typedef redefinition' errors seen in model.h"""
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
        
        if "#ifndef" in content[:100]:
            return False

        guard_name = f"GUARD_{filename.replace('.', '_').upper()}"
        new_content = f"#ifndef {guard_name}\n#define {guard_name}\n\n{content}\n\n#endif\n"
        
        with open(path, 'w') as f:
            f.write(new_content)
        return True

    def scan_symbols(self):
        """Scans for structs/enums to fix 'unknown type name' errors"""
        patterns = [
            r'((?:typedef\s+)?(?:struct|enum)\s*([\w\d_]*)\s*\{[^}]+\}\s*([\w\d_]*)\s*;)',
            r'(typedef\s+[\w\d_]+\s+([\w\d_]+)\s*;)'
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

    def harmonize_file(self, path, filename):
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
        orig_content = content

        # Fix includes
        for old, new in self.renames.items():
            content = content.replace(f'#include <{old}>', f'#include "{new}"')
            content = content.replace(f'#include "{old}"', f'#include "{new}"')

        # CRITICAL: Do NOT inject into model.h or structs.h to avoid the redefinition errors in log.txt
        forbidden = ["model.h", "structs.h", "enums.h", "functions.h", "ucode.h", "sp.h"]
        if any(f in filename for f in forbidden):
            if content != orig_content:
                with open(path, 'w') as f: f.write(content)
            return content != orig_content

        # Smart injection for missing types
        potential_types = set(re.findall(r'\b(BK[\w\d_]+|Struct[\w\d_]+)\b', content))
        needed = []
        for t in potential_types:
            if t in self.symbol_db and f"struct {t}" not in content and f"typedef struct {t}" not in content:
                needed.append(f"#ifndef _G_{t}\n#define _G_{t}\n{self.symbol_db[t]}\n#endif")

        if needed:
            injection = "\n// --- HARMONIZER v3.5 ---\n" + "\n".join(needed) + "\n"
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

    h = SourceHarmonizer(android_cpp)
    # 1. Physical Rename
    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f in h.renames:
                os.rename(os.path.join(root, f), os.path.join(root, h.renames[f]))

    # 2. Guard Enforce
    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f.endswith('.h'): h.enforce_header_guards(os.path.join(root, f), f)

    # 3. Harmonize
    h.scan_symbols()
    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f.endswith(('.c', '.h')): h.harmonize_file(os.path.join(root, f), f)

if __name__ == "__main__":
    prepare_source()
