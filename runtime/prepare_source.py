import os
import shutil
import re

class SourceHarmonizerV6_8:
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
        Safe-Type Guard: A surgical approach to stripping orphaned logic.
        Uses an expanded type whitelist and a brace-depth tracker to ensure
        we only remove executable code found in the global scope.
        """
        print("  [>] Logic Fix: Applying Safe-Type Structural Guard...")
        # Expanded whitelist including N64 specific types and pointers
        types = [
            's8','u8','s16','u16','s32','u32','s64','u64','f32','f64',
            'void','int','char','float','double','long','short','unsigned','signed',
            'static','extern','typedef','struct','enum','union','const','volatile',
            'Mtx','Vtx','Gfx','LookAt','Hilite','Lights','u_long','u_short'
        ]
        type_pattern = r'^(' + '|'.join(types) + r')[\s\*]'
        
        cleaned_count = 0
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: lines = file.readlines()
                    
                    new_lines = []
                    modified = False
                    brace_depth = 0
                    
                    for line in lines:
                        trimmed = line.strip()
                        # Track braces to know if we are in global scope (depth 0)
                        brace_depth += line.count('{') - line.count('}')
                        
                        # Identify potential orphaned logic (function calls or math) in global scope
                        is_executable = re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*\([^;]*\);', trimmed) or \
                                        re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*=[^=;]+;', trimmed)
                        
                        # Only strip if: 1. It looks like logic, 2. It's global scope, 3. It's not a known type
                        if brace_depth <= 0 and is_executable and not re.match(type_pattern, trimmed):
                            # Ensure we don't strip common macros like GFX_...
                            if not trimmed.isupper():
                                modified = True
                                continue 
                        
                        new_lines.append(line)
                    
                    if modified:
                        with open(path, 'w') as file: file.writelines(new_lines)
                        cleaned_count += 1
        print(f"      [!] Safe-stripped logic in {cleaned_count} files.")

    def patch_cmake(self):
        print("  [>] Logic Fix: Updating CMake discovery (v6.8)...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            content = re.sub(r'# --- Harmonizer v6\..*?# ---+', '', content, flags=re.DOTALL)
            injection = (
                "\n# --- Harmonizer v6.8 Total Discovery ---\n"
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
        print(f"      [!] Fixed {patched} files.")

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
        print("--- Harmonizer v6.8: Safe-Type Integrity Fix ---")
        self.sync_files()
        self.fix_static_conflicts()
        self.repair_source()
        self.repair_structural_syntax()
        self.patch_cmake()
        print("--- v6.8 Complete ---")

if __name__ == "__main__":
    ROOT = "Android/app/src/main/cpp"
    DECOMP = "decomp-files"
    if not os.path.exists(DECOMP): DECOMP = "decomp"
    h = SourceHarmonizerV6_8(ROOT, DECOMP)
    h.run()
