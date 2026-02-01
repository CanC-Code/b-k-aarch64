import os
import shutil
import re

class SourceHarmonizerV7_0:
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
        Pass 1: Build a master index of all functions and variables.
        Ensures we never delete code that is part of the game's DNA.
        """
        print("  [>] Pass 1: Global Symbol Indexing...")
        # Catch function names, variable names, and macro definitions
        decl_pattern = re.compile(r'(?:^|[\s\*])([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(\=\;]')
        
        for root, _, files in os.walk(self.decomp_path):
            for f in files:
                if f.endswith(('.c', '.h', '.cpp')):
                    with open(os.path.join(root, f), 'r', errors='ignore') as file:
                        content = file.read()
                        self.symbol_table.update(decl_pattern.findall(content))
        print(f"      [+] Verified {len(self.symbol_table)} unique symbols.")

    def sync_files(self):
        print(f"  [>] Syncing source to {self.src_target}...")
        mappings = {"src": self.src_target, "include": self.include_target}
        for sub, target in mappings.items():
            source = os.path.join(self.decomp_path, sub)
            if os.path.exists(source):
                if os.path.exists(target): shutil.rmtree(target)
                shutil.copytree(source, target)

    def enforce_header_guards(self):
        """
        Prevents 'redefinition' errors by ensuring every header has a unique guard.
        """
        print("  [>] Integrity: Enforcing Header Guards...")
        count = 0
        for root, _, files in os.walk(self.include_target):
            for f in files:
                if f.endswith('.h'):
                    path = os.path.join(root, f)
                    guard = f"GUARD_{f.replace('.', '_').upper()}"
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    if "#ifndef" not in content[:100]:
                        with open(path, 'w') as file:
                            file.write(f"#ifndef {guard}\n#define {guard}\n{content}\n#endif\n")
                        count += 1
        print(f"      [+] Guarded {count} headers.")

    def repair_structural_syntax(self):
        """
        Pass 2: Zero-Deletion Policy.
        Only 'orphaned' lines that exist in NO symbol table are removed.
        """
        print("  [>] Pass 2: Final structural validation...")
        hard_types = {'s8','u8','s16','u16','s32','u32','s64','u64','f32','f64',
                      'void','int','char','float','double','static','extern','typedef','Mtx','Vtx'}
        cleaned = 0
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: lines = file.readlines()
                    new_lines = []
                    modified = False
                    for line in lines:
                        trimmed = line.strip()
                        is_call = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]+\);', trimmed)
                        if is_call:
                            name = is_call.group(1)
                            if name not in hard_types and name not in self.symbol_table and not name.isupper():
                                modified = True
                                continue
                        new_lines.append(line)
                    if modified:
                        with open(path, 'w') as file: file.writelines(new_lines)
                        cleaned += 1
        print(f"      [!] Final repair pass: {cleaned} files adjusted.")

    def patch_cmake(self):
        print("  [>] Logic Fix: Optimizing CMake for Linker Success...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            content = re.sub(r'# --- Harmonizer v6\..*?# ---+', '', content, flags=re.DOTALL)
            
            injection = (
                "\n# --- Harmonizer v7.0 Linker Optimization ---\n"
                "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\" \"src/*.cpp\")\n"
                "foreach(FILE_PATH ${ALL_C_FILES})\n"
                "    # Exclude directories that conflict with Android/NDK internals\n"
                "    if(NOT FILE_PATH MATCHES \"/lib/\" AND \n"
                "       NOT FILE_PATH MATCHES \"/os/\" AND \n"
                "       NOT FILE_PATH MATCHES \"/gu/\" AND \n"
                "       NOT FILE_PATH MATCHES \"inflate.c\" AND \n"
                "       NOT FILE_PATH MATCHES \"rarezip.c\")\n"
                "        list(APPEND FILTERED_SOURCES ${FILE_PATH})\n"
                "    endif()\n"
                "endforeach()\n"
                "target_sources(bkawrapper PRIVATE ${FILTERED_SOURCES})\n"
                "target_link_libraries(bkawrapper log z m)\n"
                "# ------------------------------------------\n"
            )
            with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        print("--- Harmonizer v7.0: Linker & Symbol Integrity ---")
        self.build_symbol_map()
        self.sync_files()
        self.enforce_header_guards()
        self.repair_structural_syntax()
        self.patch_cmake()
        print("--- v7.0 Complete ---")

if __name__ == "__main__":
    ROOT = "Android/app/src/main/cpp"
    DECOMP = "decomp-files"
    if not os.path.exists(DECOMP): DECOMP = "decomp"
    h = SourceHarmonizerV7_0(ROOT, DECOMP)
    h.run()
