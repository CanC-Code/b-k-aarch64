import os
import shutil
import re

class SourceHarmonizerV6_7:
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
        Context-Aware Guard: Specifically targets orphaned logic artifacts.
        It removes lines that are clearly function calls (e.g. func(val);) 
        but ONLY if they do not start with a known C type or keyword.
        """
        print("  [>] Logic Fix: Applying Context-Aware Structural Guard...")
        # Common N64/C types to protect
        protected_types = r'^(s8|u8|s16|u16|s32|u32|s64|u64|f32|f64|void|int|char|float|double|static|extern|typedef|struct|enum)'
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
                        trimmed = line.strip()
                        # If it's a call with arguments but NOT a declaration
                        is_call = re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]+\);', trimmed)
                        is_decl = re.match(protected_types, trimmed)
                        
                        if is_call and not is_decl:
                            # This is likely an orphaned call like mapSpecificFlags_set(0x10, 0);
                            modified = True
                            continue 
                        new_lines.append(line)
                    
                    if modified:
                        with open(path, 'w') as file: 
                            file.writelines(new_lines)
                        cleaned_count += 1
        print(f"      [!] Cleaned orphaned logic in {cleaned_count} files.")

    def patch_cmake(self):
        print("  [>] Logic Fix: Updating CMake discovery (v6.7)...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            content = re.sub(r'# --- Harmonizer v6\..*?# ---+', '', content, flags=re.DOTALL)
            
            injection = (
                "\n# --- Harmonizer v6.7 Total Discovery ---\n"
                "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\" \"src/*.cpp\")\n"
                "foreach(FILE_PATH ${ALL_C_FILES})\n"
                "    # Exclude lib/ and internal N64 OS/Graphics utils to avoid NDK conflicts\n"
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
        print(f"      [!] Fixed {patched} files.")

    def fix_function_pointer_casts(self):
        builder_cpp = os.path.join(self.ultra_target, "otr_builder.cpp")
        if os.path.exists(builder_cpp):
            with open(builder_cpp, 'r') as f: content = f.read()
            new_content = content.replace("decompress_rare_asset", "(void (*)(u8 *, u8 *))decompress_rare_asset")
            with open(builder_cpp, 'w') as f: f.write(new_content)

    def fix_conflicting_signatures(self):
        target_h = os.path.join(self.ultra_target, "rare_decompression.h")
        if os.path.exists(target_h):
            with open(target_h, 'r') as f: content = f.read()
            new_content = content.replace("s32 decompress_rare_asset", "void decompress_rare_asset")
            with open(target_h, 'w') as f: f.write(new_content)

    def repair_source(self):
        print("  [>] Logic Fix: Repairing array initializers...")
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
        print("--- Harmonizer v6.7: Context-Aware Fix ---")
        self.sync_files()
        self.fix_conflicting_signatures()
        self.fix_function_pointer_casts()
        self.fix_static_conflicts()
        self.repair_source()
        self.repair_structural_syntax()
        self.patch_cmake()
        print("--- v6.7 Complete ---")

if __name__ == "__main__":
    ROOT = "Android/app/src/main/cpp"
    DECOMP = "decomp-files"
    if not os.path.exists(DECOMP): DECOMP = "decomp"
    h = SourceHarmonizerV6_7(ROOT, DECOMP)
    h.run()
