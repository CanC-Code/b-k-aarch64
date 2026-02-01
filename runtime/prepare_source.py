import os
import shutil
import re

class SourceHarmonizerV6_0:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.ultra_target = os.path.join(android_path, "ultra")
        self.cmake_file = os.path.join(android_path, "CMakeLists.txt")

    def sync_files(self):
        print(f"  [>] Syncing source from {self.decomp_path}...")
        mappings = {"src": self.src_target, "include": self.include_target}
        for sub, target in mappings.items():
            source = os.path.join(self.decomp_path, sub)
            if os.path.exists(source):
                if os.path.exists(target): shutil.rmtree(target)
                shutil.copytree(source, target)
                print(f"      [+] Synced {sub}/ folder.")

    def patch_cmake(self):
        """
        Critical Logic Fix: Updates CMakeLists.txt to ensure all 130+ 
        game source files are compiled, resolving the 'undefined symbol' errors.
        """
        print("  [>] Logic Fix: Injecting recursive source discovery into CMake...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            
            # This injection ensures Ninja finds every .c file in the src subdirectories
            injection = (
                "\n# --- Harmonizer v6.0 Source Discovery ---\n"
                "file(GLOB_RECURSE GAME_SOURCES \"src/*.c\")\n"
                "target_sources(bkawrapper PRIVATE ${GAME_SOURCES})\n"
                "# ---------------------------------------\n"
            )
            
            if "GAME_SOURCES" not in content:
                with open(self.cmake_file, 'a') as f: f.write(injection)
                print("      [!] CMakeLists.txt patched to include all game sources.")
            else:
                print("      [>] CMake already contains source discovery logic.")

    def fix_static_conflicts(self):
        print("  [>] Logic Fix: Harmonizing static function declarations...")
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
        print(f"      [!] Fixed static conflicts in {patched} files.")

    def fix_function_pointer_casts(self):
        builder_cpp = os.path.join(self.ultra_target, "otr_builder.cpp")
        if os.path.exists(builder_cpp):
            with open(builder_cpp, 'r') as f: content = f.read()
            new_content = content.replace("decompress_rare_asset", "(void (*)(u8 *, u8 *))decompress_rare_asset")
            if new_content != content:
                with open(builder_cpp, 'w') as f: f.write(new_content)

    def fix_conflicting_signatures(self):
        target_h = os.path.join(self.ultra_target, "rare_decompression.h")
        if os.path.exists(target_h):
            with open(target_h, 'r') as f: content = f.read()
            new_content = content.replace("s32 decompress_rare_asset", "void decompress_rare_asset")
            with open(target_h, 'w') as f: f.write(new_content)

    def repair_source(self):
        print("  [>] Logic Fix: Repairing legacy C array initializers...")
        patched = 0
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    pattern = r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);'
                    if re.search(pattern, content):
                        if '<string.h>' not in content: content = '#include <string.h>\n' + content
                        new_content = re.sub(pattern, r'\1 \2[\3]; memmove(\2, \4, \3);', content)
                        with open(path, 'w') as file: file.write(new_content)
                        patched += 1
        print(f"      [!] Repaired {patched} files.")

    def fix_header_linkage(self):
        target = "rare_decompression.h"
        dest = os.path.join(self.ultra_target, target)
        search_roots = [self.decomp_path, self.android_path, "."]
        for s_root in search_roots:
            for root, _, files in os.walk(s_root):
                if target in files:
                    os.makedirs(self.ultra_target, exist_ok=True)
                    shutil.copy2(os.path.join(root, target), dest)
                    return True
        return False

    def run(self):
        print("--- Harmonizer v6.0: Full Project Compilation ---")
        self.sync_files()
        self.fix_header_linkage()
        self.fix_conflicting_signatures()
        self.fix_function_pointer_casts()
        self.fix_static_conflicts()
        self.repair_source()
        self.patch_cmake() # Critical addition
        print("--- v6.0 Complete ---")

if __name__ == "__main__":
    ROOT = "Android/app/src/main/cpp"
    DECOMP = "decomp-files"
    if not os.path.exists(DECOMP): DECOMP = "decomp"
    h = SourceHarmonizerV6_0(ROOT, DECOMP)
    h.run()
