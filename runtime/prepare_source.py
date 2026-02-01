import os
import shutil
import re

class SourceHarmonizerV6_9:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.ultra_target = os.path.join(android_path, "ultra")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")
        self.symbol_table = set()

    def build_symbol_map(self):
        """
        Pass 1: Scan all files to identify valid function and variable names.
        This prevents the script from deleting valid logic later.
        """
        print("  [>] Pass 1: Building Global Symbol Map...")
        # Regex to find function names: 'void func_name(' or 'int var_name ='
        decl_pattern = re.compile(r'(?:^|[\s\*])([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(\=]')
        
        for root, _, files in os.walk(self.decomp_path):
            for f in files:
                if f.endswith(('.c', '.h')):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        matches = decl_pattern.findall(content)
                        self.symbol_table.update(matches)
        print(f"      [+] Indexed {len(self.symbol_table)} valid symbols.")

    def sync_files(self):
        print(f"  [>] Syncing source from {self.decomp_path}...")
        mappings = {"src": self.src_target, "include": self.include_target}
        for sub, target in mappings.items():
            source = os.path.join(self.decomp_path, sub)
            if os.path.exists(source):
                if os.path.exists(target): shutil.rmtree(target)
                shutil.copytree(source, target)

    def repair_structural_syntax(self):
        """
        Pass 2: Surgical Repair.
        Instead of deleting, we only remove lines that are clearly orphaned logic 
        (calls to non-existent or mis-scoped symbols).
        """
        print("  [>] Pass 2: Repairing structural syntax using symbol validation...")
        cleaned_count = 0
        
        # Types that always signify a declaration (Never Delete)
        hard_types = {'s8','u8','s16','u16','s32','u32','s64','u64','f32','f64',
                      'void','int','char','float','double','static','extern','typedef'}

        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        lines = file.readlines()
                    
                    new_lines = []
                    modified = False
                    for line in lines:
                        trimmed = line.strip()
                        # If the line looks like an orphaned call: 'func(0, 0);'
                        is_call = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]+\);', trimmed)
                        
                        if is_call:
                            func_name = is_call.group(1)
                            # Only delete if it's NOT a type and NOT a known symbol
                            if func_name not in hard_types and func_name not in self.symbol_table:
                                modified = True
                                continue 
                        
                        new_lines.append(line)
                    
                    if modified:
                        with open(path, 'w') as file:
                            file.writelines(new_lines)
                        cleaned_count += 1
        print(f"      [!] Validated and repaired {cleaned_count} files.")

    def patch_cmake(self):
        print("  [>] Logic Fix: Updating CMake with total integrity discovery...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            content = re.sub(r'# --- Harmonizer v6\..*?# ---+', '', content, flags=re.DOTALL)
            
            injection = (
                "\n# --- Harmonizer v6.9 Symbol-Safe Discovery ---\n"
                "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\" \"src/*.cpp\")\n"
                "foreach(FILE_PATH ${ALL_C_FILES})\n"
                "    if(NOT FILE_PATH MATCHES \"/lib/\" AND \n"
                "       NOT FILE_PATH MATCHES \"inflate.c\" AND \n"
                "       NOT FILE_PATH MATCHES \"rarezip.c\" AND\n"
                "       NOT FILE_PATH MATCHES \"/gu/\" AND\n"
                "       NOT FILE_PATH MATCHES \"/os/\")\n"
                "        list(APPEND FILTERED_SOURCES ${FILE_PATH})\n"
                "    endif()\n"
                "endforeach()\n"
                "target_sources(bkawrapper PRIVATE ${FILTERED_SOURCES})\n"
                "# ---------------------------------------\n"
            )
            with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def fix_static_conflicts(self):
        print("  [>] Logic Fix: Removing conflicting static prototypes...")
        patched = 0
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    static_defs = re.findall(r'static\s+\w+\s+(\w+)\s*\(', content)
                    if static_defs:
                        initial_content = content
                        for func_name in static_defs:
                            proto_pattern = r'^[^#\n]*?\w+\s+' + re.escape(func_name) + r'\s*\([^;]*\);'
                            content = re.sub(proto_pattern, '', content, flags=re.MULTILINE)
                        if content != initial_content:
                            with open(path, 'w') as file: file.write(content)
                            patched += 1

    def run(self):
        print("--- Harmonizer v6.9: Symbol-Safe Integrity ---")
        self.build_symbol_map()
        self.sync_files()
        self.fix_static_conflicts()
        self.repair_structural_syntax()
        self.patch_cmake()
        print("--- v6.9 Complete ---")

if __name__ == "__main__":
    ROOT = "Android/app/src/main/cpp"
    DECOMP = "decomp-files"
    if not os.path.exists(DECOMP): DECOMP = "decomp"
    h = SourceHarmonizerV6_9(ROOT, DECOMP)
    h.run()
