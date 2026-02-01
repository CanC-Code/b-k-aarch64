import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {}
        # Core mappings for NDK compatibility
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}

    def enforce_header_guards(self, path, filename):
        """Mandatory for stopping recursive inclusions like enums.h and structs.h"""
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
        
        if "#ifndef" in content and "#define" in content:
            return False

        guard_name = f"GUARD_{filename.replace('.', '_').upper()}_{os.urandom(2).hex()}"
        new_content = f"#ifndef {guard_name}\n#define {guard_name}\n\n{content}\n\n#endif\n"
        
        with open(path, 'w') as f:
            f.write(new_content)
        return True

    def scan_symbols(self):
        """Builds a database of structs and enums to fix 'unknown type' errors"""
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
                                if name and name not in self.symbol_db:
                                    self.symbol_db[name] = full_def

    def harmonize_file(self, path, filename):
        with open(path, 'r', errors='ignore') as f:
            content = f.read()

        orig_content = content

        # 1. Update Include Paths
        for old_h, new_h in self.renames.items():
            content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')
            content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

        # 2. Critical Exclusion: Do NOT inject into files that are already redefinition targets
        # This fixes the 'redefinition of sprite' error in structs.h/sp.h
        skip_injection_files = ["structs.h", "sp.h", "enums.h", "ucode.h", "functions.h", "ultra64.h"]
        if any(x in filename for x in skip_injection_files):
            if content != orig_content:
                with open(path, 'w') as f: f.write(content)
            return content != orig_content

        # 3. Smart Injection (only if type is missing)
        potential_types = set(re.findall(r'\b([sS][\w\d_]+|[a-zA-Z_][\w\d_]*_t|BK[\w]+|Struct[\w]+)\b', content))
        needed_defs = []
        for type_name in potential_types:
            # Verify the type isn't already textually present in the file
            if type_name in self.symbol_db and f" {type_name}" not in content:
                guard = f"_GUARD_{type_name}"
                needed_defs.append(f"#ifndef {guard}\n#define {guard}\n{self.symbol_db[type_name]}\n#endif")

        if needed_defs:
            injection = "\n// --- HARMONIZER v3.4 (DEDUPLICATED) ---\n" + "\n".join(needed_defs) + "\n"
            match = re.search(r'#include.*?\n', content)
            pos = match.end() if match else 0
            content = content[:pos] + injection + content[pos:]

        if content != orig_content:
            with open(path, 'w') as f: f.write(content)
            return True
        return False

def prepare_source():
    print("--- Final Source Harmonization v3.4 ---")
    android_cpp = "Android/app/src/main/cpp"

    for sub in ["src", "include"]:
        target = os.path.join(android_cpp, sub)
        if os.path.exists(target): shutil.rmtree(target)
        os.makedirs(target, exist_ok=True)

    shutil.copytree("decomp-files/include", os.path.join(android_cpp, "include"), dirs_exist_ok=True)
    shutil.copytree("decomp-files/src", os.path.join(android_cpp, "src"), dirs_exist_ok=True)

    harmonizer = SourceHarmonizer(android_cpp)
    
    # Process Headers
    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f.endswith('.h'):
                harmonizer.enforce_header_guards(os.path.join(root, f), f)

    harmonizer.scan_symbols()
    
    # Process all files
    patched = 0
    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f.endswith(('.c', '.h')):
                if harmonizer.harmonize_file(os.path.join(root, f), f):
                    patched += 1

    print(f"--- Finished: Patched {patched} files ---")

if __name__ == "__main__":
    prepare_source()
