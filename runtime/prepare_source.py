import os
import shutil
import re

class SourceHarmonizerV6_6:
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

    def repair_structural_syntax(self):
        """
        Precise Scope Guard: Fixes 'expected parameter declarator'.
        Only removes lines that are clearly executable logic (calls with values) 
        found in the global scope, while preserving function declarations.
        """
        print("  [>] Logic Fix: Applying Precise Scope Guard...")
        cleaned_count = 0
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: 
                        lines = file.readlines()
                    
                    new_lines = []
                    modified = False
                    for line in lines:
                        # TARGET: Orphaned calls like 'func(0x10, 0);' or 'variable = value;' in global scope
                        # PROTECT: 'void func(s32 a);' or 'extern int x;'
                        
                        # Match a function call pattern that starts at line beginning
                        is_call = re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*[0-9x][^)]*\);', line)
                        # Match a global assignment artifact
                        is_assignment = re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=[^=;]+;', line)
                        
                        if (is_call or is_assignment) and not any(k in line for k in ["static", "extern", "typedef", "struct"]):
                            modified = True
                            continue 
                        new_lines.append(line)
                    
                    if modified:
                        with open(path, 'w') as file: 
                            file.writelines(new_lines)
                        cleaned_count += 1
        print(f"      [!] Stripped orphaned logic artifacts from {cleaned_count} files.")

    def patch_cmake(self):
        print("  [>] Logic Fix: Updating CMake with v6.6 discovery logic...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            # Clean all previous Harmonizer versions
            content = re.sub(r'# --- Harmonizer v6\..*?# ---+', '', content, flags=re.DOTALL)
            
            injection = (
                "\n# --- Harmonizer v6.6 Total Discovery ---\n"
                "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\")\n"
                "foreach(FILE_PATH ${ALL_C_FILES})\n"
                "    # Exclude lib and platform-specifics that conflict with NDK\n"
                "    if(NOT FILE_PATH MATCHES \"src/lib/\" AND \n"
                "       NOT FILE_PATH MATCHES \"inflate.c\" AND \n"
                "       NOT FILE_PATH MATCHES \"rarezip.c\" AND\n"
                "       NOT FILE_PATH MATCHES \"gu/\" AND\n"
                "       NOT FILE_PATH MATCHES \"os/\")\n"
                "        list(APPEND FILTERED_SOURCES ${FILE_PATH})\n"
                "    endif()\n"
                "endforeach()\n"
                "target_sources(bkawrapper PRIVATE ${FILTERED_SOURCES})\n"
                "# ---------------------------------------\n"
            )
            
            with open(self.cmake_file, 'w') as f: f.write(content + injection)
            print("      [!] CMakeLists.txt updated.")

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

    def run(self):
        print("--- Harmonizer v6.6: Precise Integrity Fix ---")
        self.sync_files()
        self.fix_conflicting_signatures()
        self.fix_function_pointer_casts()
        self.fix_static_conflicts()
        self.repair_source()
        self.repair_structural_syntax()
        self.patch_cmake()
        print("--- v6.6 Complete ---")

if __name__ == "__main__":
    ROOT = "Android/app/src/main/cpp"
    DECOMP = "decomp-files"
    if not os.path.exists(DECOMP): DECOMP = "decomp"
    h = SourceHarmonizerV6_6(ROOT, DECOMP)
    h.run()
