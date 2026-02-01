import os
import shutil
import re

class SourceHarmonizerV7_2:
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

    def repair_structural_syntax(self):
        """
        Scope-Strict Guard: Any line in the global scope (brace depth 0) 
        containing logic (calls/assignments) that doesn't start with a type 
        is a decompilation artifact and must be removed.
        """
        print("  [>] Logic Fix: Applying Scope-Strict Structural Guard...")
        
        # Types that define a valid global declaration
        valid_starts = r'^(s8|u8|s16|u16|s32|u32|s64|u64|f32|f64|void|int|char|float|double|static|extern|typedef|struct|enum|const|Mtx|Vtx|Gfx|LookAt)'
        
        cleaned_count = 0
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: 
                        lines = file.readlines()
                    
                    new_lines = []
                    modified = False
                    brace_depth = 0
                    
                    for line in lines:
                        trimmed = line.strip()
                        
                        # Track scope depth
                        brace_depth += line.count('{') - line.count('}')
                        
                        # If we are at the top level (global scope)
                        if brace_depth == 0 and not line.startswith('}'):
                            # Does it look like an executable statement? (ends in ; and has logic symbols)
                            is_logic = re.search(r'[\(\=\+\-]', trimmed) and trimmed.endswith(';')
                            # Does it NOT start with a valid C type?
                            is_not_decl = not re.match(valid_starts, trimmed)
                            
                            if is_logic and is_not_decl:
                                # This is an orphaned artifact (e.g. "func(0,0);")
                                modified = True
                                continue 
                        
                        new_lines.append(line)
                    
                    if modified:
                        with open(path, 'w') as file: 
                            file.writelines(new_lines)
                        cleaned_count += 1
        print(f"      [!] Stripped global-scope artifacts from {cleaned_count} files.")

    def patch_cmake(self):
        print("  [>] Logic Fix: Updating CMake for v7.2...")
        if os.path.exists(self.cmake_file):
            with open(self.cmake_file, 'r') as f: content = f.read()
            content = re.sub(r'# --- Harmonizer v[0-9]\.[0-9].*?# ---+', '', content, flags=re.DOTALL)
            
            injection = (
                "\n# --- Harmonizer v7.2 Discovery ---\n"
                "file(GLOB_RECURSE ALL_C_FILES \"src/*.c\" \"src/*.cpp\")\n"
                "foreach(FILE_PATH ${ALL_C_FILES})\n"
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
                "# ----------------------------------\n"
            )
            with open(self.cmake_file, 'w') as f: f.write(content + injection)

    def run(self):
        print("--- Harmonizer v7.2: Scope-Strict Fix ---")
        self.sync_files()
        self.repair_structural_syntax()
        self.patch_cmake()
        print("--- v7.2 Complete ---")

if __name__ == "__main__":
    ROOT = "Android/app/src/main/cpp"
    DECOMP = "decomp-files"
    if not os.path.exists(DECOMP): DECOMP = "decomp"
    h = SourceHarmonizerV7_2(ROOT, DECOMP)
    h.run()
