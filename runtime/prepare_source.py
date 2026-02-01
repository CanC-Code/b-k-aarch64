import os
import shutil
import re

class SourceHarmonizerV7_5:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")
        self.global_symbols = set()

    def index_all_symbols(self):
        print("  [>] Pass 1: Massive Project Indexing...")
        patterns = [
            re.compile(r'^[a-zA-Z_]\w*\s+([a-zA-Z_]\w*)\s*\(', re.MULTILINE),
            re.compile(r'^[a-zA-Z_]\w*\s+([a-zA-Z_]\w*)\s*[;=\[]', re.MULTILINE),
            re.compile(r'#define\s+([a-zA-Z_]\w*)')
        ]
        for root, _, files in os.walk(self.decomp_path):
            for f in files:
                if f.endswith(('.c', '.h', '.cpp')):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        for p in patterns:
                            self.global_symbols.update(p.findall(content))
        self.global_symbols.update(['Actor', 'Gfx', 'Mtx', 'Vtx', 'u32', 's32', 'f32', 'TRUE', 'FALSE', 'NULL', 'u8', 's8', 'bool'])
        print(f"      [+] Indexed {len(self.global_symbols)} symbols.")

    def fix_static_conflicts(self):
        """
        Pass 2: Resolves 'static declaration follows non-static' errors.
        Identifies static definitions and ensures forward declarations match.
        """
        print("  [>] Pass 2: Harmonizing Static Declarations...")
        # Matches: static return_type func_name(args) {
        static_def_pattern = re.compile(r'^static\s+[\w\s\*]+\s+([a-zA-Z_]\w*)\s*\(', re.MULTILINE)
        patched = 0

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    
                    found_statics = static_def_pattern.findall(content)
                    if not found_statics: continue

                    modified = False
                    for func_name in found_statics:
                        # Find non-static forward declarations of this specific static function
                        # Pattern: [not static] return_type func_name(args);
                        fwd_decl_pattern = re.compile(r'^(?!static|#)([\w\s\*]+\s+' + re.escape(func_name) + r'\s*\([^;]*\);)', re.MULTILINE)
                        if fwd_decl_pattern.search(content):
                            content = fwd_decl_pattern.sub(r'static \1', content)
                            modified = True
                    
                    if modified:
                        with open(path, 'w') as file: file.write(content)
                        patched += 1
        print(f"      [!] Synchronized static declarations in {patched} files.")

    def repair_legacy_initializers(self):
        print("  [>] Pass 3: Repairing Legacy Array Initializers...")
        pattern = re.compile(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);')
        patched = 0
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    if pattern.search(content):
                        if '<string.h>' not in content: content = '#include <string.h>\n' + content
                        new_content = pattern.sub(r'\1 \2[\3]; memmove(\2, \4, \3);', content)
                        with open(path, 'w') as file: file.write(new_content)
                        patched += 1
        print(f"      [!] Array initializers repaired: {patched} files.")

    def run(self):
        print("--- Harmonizer v7.5: Static Declaration Resolver ---")
        self.index_all_symbols()
        # Note: sync_files should be run before modifications if refreshing from decomp
        self.fix_static_conflicts()
        self.repair_legacy_initializers()
        # Pass 3/4: Structural Guards from previous versions remain active
        print("--- v7.5 Complete ---")

if __name__ == "__main__":
    h = SourceHarmonizerV7_5("Android/app/src/main/cpp", "decomp-files")
    h.run()
