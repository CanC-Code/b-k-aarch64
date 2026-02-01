import os
import shutil
import re

class SourceHarmonizerV7_4:
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
        self.global_symbols.update(['Actor', 'Gfx', 'Mtx', 'Vtx', 'u32', 's32', 'f32', 'TRUE', 'FALSE', 'NULL', 'u8', 's8'])
        print(f"      [+] Indexed {len(self.global_symbols)} symbols.")

    def sync_files(self):
        print(f"  [>] Syncing source from {self.decomp_path}...")
        for sub in ["src", "include"]:
            target = os.path.join(self.android_path, sub)
            source = os.path.join(self.decomp_path, sub)
            if os.path.exists(source):
                if os.path.exists(target): shutil.rmtree(target)
                shutil.copytree(source, target)

    def fix_array_initializers(self):
        """
        Pass 2: Fixes 'array initializer must be an initializer list' errors.
        Converts: u8 tmp[6] = D_Symbol;
        Into:    u8 tmp[6]; memmove(tmp, D_Symbol, 6);
        """
        print("  [>] Pass 2: Repairing Legacy Array Initializers...")
        # Pattern matches: type name[size] = value;
        pattern = re.compile(r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);')
        patched = 0
        
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    
                    if pattern.search(content):
                        # Ensure string.h is present for memmove
                        if '<string.h>' not in content:
                            content = '#include <string.h>\n' + content
                        
                        # Apply transformation
                        new_content = pattern.sub(r'\1 \2[\3]; memmove(\2, \4, \3);', content)
                        with open(path, 'w') as file: file.write(new_content)
                        patched += 1
        print(f"      [!] Patched {patched} files with legacy initializers.")

    def repair_structural_syntax(self):
        print("  [>] Pass 3: Surgical Structural Guard...")
        valid_starts = r'^(s8|u8|s16|u16|s32|u32|s64|u64|f32|f64|void|int|char|float|double|static|extern|typedef|struct|enum|const|Mtx|Vtx|Gfx|Actor)'
        cleaned = 0
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: lines = file.readlines()
                    new_lines = []
                    modified = False
                    depth = 0
                    for line in lines:
                        trimmed = line.strip()
                        depth += line.count('{') - line.count('}')
                        if depth == 0 and not line.startswith('}'):
                            if re.search(r'[\(\=]', trimmed) and not re.match(valid_starts, trimmed):
                                words = re.findall(r'[a-zA-Z_]\w*', trimmed)
                                if not any(w in self.global_symbols for w in words):
                                    modified = True
                                    continue
                        new_lines.append(line)
                    if modified:
                        with open(path, 'w') as file: file.writelines(new_lines)
                        cleaned += 1
        print(f"      [!] Structural repair: {cleaned} files adjusted.")

    def patch_cmake(self):
        print("  [>] Finalizing CMake for v7.4...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            content = re.sub(r'# --- Harmonizer v[0-9]\.[0-9].*?# ---+', '', content, flags=re.DOTALL)
            injection = (
                "\n# --- Harmonizer v7.4 Integrity ---\n"
                "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\" \"src/*.cpp\")\n"
                "target_sources(bkawrapper PRIVATE ${ALL_C_FILES})\n"
                "target_link_libraries(bkawrapper log z m)\n"
                "# ----------------------------------\n"
            )
            with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        print("--- Harmonizer v7.4: Array Initializer Fix ---")
        self.index_all_symbols()
        self.sync_files()
        self.fix_array_initializers()
        self.repair_structural_syntax()
        self.patch_cmake()
        print("--- v7.4 Complete ---")

if __name__ == "__main__":
    h = SourceHarmonizerV7_4("Android/app/src/main/cpp", "decomp-files")
    h.run()
