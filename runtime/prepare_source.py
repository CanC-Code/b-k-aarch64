import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {}
        # Maps problematic legacy headers to safe local names to avoid NDK collisions
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}

    def enforce_header_guards(self, path, filename):
        """
        Physically adds #ifndef guards to every header.
        This is critical to stop the 'redefinition of sfx_e' errors found in log.txt.
        """
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
        
        # Check if the file already has guards to avoid double-wrapping
        if content.strip().startswith("#ifndef"):
            return False

        # Generate a unique guard name based on the filename to ensure no collisions
        safe_name = filename.replace('.', '_').replace('/', '_').upper()
        guard_name = f"GUARD_{safe_name}_{os.urandom(2).hex()}"
        
        new_content = f"#ifndef {guard_name}\n#define {guard_name}\n\n{content}\n\n#endif // {guard_name}\n"
        
        with open(path, 'w') as f:
            f.write(new_content)
        return True

    def scan_symbols(self):
        print("  [>] Scanning project for all global types...")
        # Patterns to identify structs, enums, and typedefs for injection
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

        # Update include paths to point to the renamed local headers
        for old_h, new_h in self.renames.items():
            content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')
            content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

        content = re.sub(r'#include\s+["<](?:2\.0L/PR/)?sched\.h[">]', '#include "game_sched.h"', content)

        # Skip type injection for core headers to prevent duplication errors
        core_headers = ["ultra64.h", "gbi.h", "mbi.h", "sptask.h", "enums.h", "ucode.h", "sp.h", "functions.h"]
        is_core_header = any(x in filename for x in core_headers)
        
        potential_types = set(re.findall(r'\b([sS][\w\d_]+|[a-zA-Z_][\w\d_]*_t|audioInfo|Bitmap|Gfx|ActorMarker|Actor)\b', content))

        needed_defs = []
        if not is_core_header:
            for type_name in potential_types:
                # Only inject if symbol exists and isn't already textually present in this file
                if type_name in self.symbol_db and f"struct {type_name}" not in content and f"typedef struct {type_name}" not in content:
                    guard = f"_GUARD_{type_name}"
                    needed_defs.append(f"#ifndef {guard}\n#define {guard}\n{self.symbol_db[type_name]}\n#endif")

        # Handle local static function prototypes
        static_funcs = re.findall(r'^static\s+[\w\*]+\s+([\w\d_]+)\s*\(', content, re.MULTILINE)
        prototypes = []
        for f in static_funcs:
            sig = re.search(r'^(static\s+[\w\*]+\s+' + re.escape(f) + r'\s*\([^)]*\))', content, re.MULTILINE)
            if sig: prototypes.append(f"{sig.group(1)};")

        if needed_defs or prototypes:
            injection = "\n// --- AUTOMATED HARMONIZER v3.3 (FINAL FIX) ---\n" + "\n".join(needed_defs + prototypes) + "\n"
            match = re.search(r'#include.*?\n', content)
            pos = match.end() if match else 0
            content = content[:pos] + injection + content[pos:]

        if content != orig_content:
            with open(path, 'w') as f: f.write(content)
            return True
        return False

def prepare_source():
    print("--- Starting Automated Source Harmonization v3.3 ---")
    android_cpp = "Android/app/src/main/cpp"

    # Wipe existing source/include directories to ensure a clean build state
    for sub in ["src", "include"]:
        target = os.path.join(android_cpp, sub)
        if os.path.exists(target): shutil.rmtree(target)
        os.makedirs(target, exist_ok=True)

    print("  [+] Syncing fresh files from decomp-files...")
    shutil.copytree("decomp-files/include", os.path.join(android_cpp, "include"), dirs_exist_ok=True)
    shutil.copytree("decomp-files/src", os.path.join(android_cpp, "src"), dirs_exist_ok=True)

    harmonizer = SourceHarmonizer(android_cpp)
    
    # 1. First, rename legacy headers to avoid Android NDK system collisions
    harmonizer.rename_physical_headers()
    
    # 2. Second, apply mandatory header guards to every header file
    print("  [>] Enforcing global header guards...")
    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f.endswith('.h'):
                harmonizer.enforce_header_guards(os.path.join(root, f), f)

    # 3. Finally, scan symbols and harmonize definitions/includes
    harmonizer.scan_symbols()
    patched = 0
    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f.endswith(('.c', '.h')):
                if harmonizer.harmonize_file(os.path.join(root, f), f):
                    patched += 1

    print(f"--- Finished: Patched {patched} files ---")

if __name__ == "__main__":
    prepare_source()
