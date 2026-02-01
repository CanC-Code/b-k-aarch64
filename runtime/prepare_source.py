
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
        # Patterns to catch structs, enums, and complex typedefs
        patterns = [
            r'((?:typedef\s+)?(?:struct|enum)\s*([\w\d_]*)\s*\{[^}]+\}\s*([\w\d_]*)\s*;)',
            r'(typedef\s+[\w\d_]+\s+([\w\d_]+)\s*;)',
            r'(struct\s+([\w\d_]+)\s*;)' # Catch forward declarations too
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

    def harmonize_file(self, path, filename):
        with open(path, 'r', errors='ignore') as f:
            content = f.read()

        orig_content = content

        # A. Header Mapping (Syncing code with renamed physical files)
        for old_h, new_h in self.renames.items():
            content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')
            content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

        content = re.sub(r'#include\s+["<](?:2\.0L/PR/)?sched\.h[">]', '#include "game_sched.h"', content)

        # B. Dependency Injection
        # Added 'ActorMarker' and more to the detection list
        is_core_header = any(x in content for x in ["ultra64.h", "gbi.h", "mbi.h"])
        potential_types = set(re.findall(r'\b([sS][\w\d_]+|[a-zA-Z_][\w\d_]*_t|audioInfo|Bitmap|Gfx|ActorMarker|Actor)\b', content))

        needed_defs = []
        if not is_core_header:
            for type_name in potential_types:
                if type_name in self.symbol_db and f"struct {type_name}" not in content:
                    guard = f"_GUARD_{type_name}"
                    needed_defs.append(f"#ifndef {guard}\n#define {guard}\n{self.symbol_db[type_name]}\n#endif")

        # C. Linkage (Static vs Extern)
        static_funcs = re.findall(r'^static\s+[\w\*]+\s+([\w\d_]+)\s*\(', content, re.MULTILINE)
        prototypes = []
        for f in static_funcs:
            sig = re.search(r'^(static\s+[\w\*]+\s+' + re.escape(f) + r'\s*\([^)]*\))', content, re.MULTILINE)
            if sig: prototypes.append(f"{sig.group(1)};")

        # Injection
        if needed_defs or prototypes:
            injection = "\n// --- AUTOMATED HARMONIZER v3 ---\n" + "\n".join(needed_defs + prototypes) + "\n"
            match = re.search(r'#include.*?\n', content)
            pos = match.end() if match else 0
            content = content[:pos] + injection + content[pos:]

        if content != orig_content:
            with open(path, 'w') as f: f.write(content)
            return True
        return False

def prepare_source():
    print("--- Starting Automated Source Harmonization v3 ---")
    android_cpp = "Android/app/src/main/cpp"

    # 1. Sync & Setup
    if os.path.exists(android_cpp): shutil.rmtree(android_cpp)
    shutil.copytree("decomp-files/include", os.path.join(android_cpp, "include"))
    shutil.copytree("decomp-files/src", os.path.join(android_cpp, "src"))

    harmonizer = SourceHarmonizer(android_cpp)

    # 2. Fix physical file names first!
    harmonizer.rename_physical_headers()

    # 3. Scan and Harmonize
    harmonizer.scan_symbols()
    patched = 0
    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f.endswith(('.c', '.h')) and harmonizer.harmonize_file(os.path.join(root, f), f):
                patched += 1

    print(f"--- Finished: Patched {patched} files ---")

if __name__ == "__main__":
    prepare_source()