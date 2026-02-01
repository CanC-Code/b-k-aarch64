import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {}
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
        
        # SACRED TYPES: These cause the redefinitions found in log.txt. 
        # [span_10](start_span)[span_11](start_span)We manually skip them to let the headers handle them naturally.[span_10](end_span)[span_11](end_span)
        self.sacred_types = ["sprite", "sfx_e", "ALLink", "ALSound", "N_ALVoice", "ALMicroTime", "Bitmap"]
        
        # CORE HEADERS: We NEVER inject into these. This prevents the loops in ultra64/enums.
        self.core_headers = ["ultra64.h", "gbi.h", "sp.h", "libaudio.h", "enums.h", "functions.h"]

    def scan_symbols(self):
        print("  [>] Scanning for project types...")
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

    def harmonize_file(self, path, filename):
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
        orig_content = content

        for old_h, new_h in self.renames.items():
            content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')

        # Logic: Only inject into non-core files to avoid the redefinition errors in log
        if filename not in self.core_headers:
            # Find all potential custom types
            potential_types = set(re.findall(r'\b(BK[\w\d_]+|[sS][\w\d_]+|ActorMarker|Gfx|Bitmap|AL[\w\d_]+)\b', content))
            needed_defs = []
            
            for type_name in potential_types:
                if type_name in self.symbol_db and type_name not in self.sacred_types:
                    # BRUTE FORCE: Wrap in unique guards so even multiple injections won't crash
                    guard = f"_HARM_DEF_{type_name}"
                    if guard not in content:
                        needed_defs.append(f"#ifndef {guard}\n#define {guard}\n{self.symbol_db[type_name]}\n#endif")

            if needed_defs:
                injection = "\n// --- HARMONIZER v4.7 ---\n" + "\n".join(needed_defs) + "\n"
                match = re.search(r'#include.*?\n', content)
                pos = match.end() if match else 0
                content = content[:pos] + injection + content[pos:]

        if content != orig_content:
            with open(path, 'w') as f: f.write(content)
            return True
        return False

def run_harmonizer():
    android_cpp = "Android/app/src/main/cpp"
    
    # SAFE WIPE: Refresh only game source, keep CMake/NativeBridge files
    for sub in ["src", "include"]:
        path = os.path.join(android_cpp, sub)
        if os.path.exists(path): shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)
    
    shutil.copytree("decomp-files/include", os.path.join(android_cpp, "include"), dirs_exist_ok=True)
    shutil.copytree("decomp-files/src", os.path.join(android_cpp, "src"), dirs_exist_ok=True)

    h = SourceHarmonizer(android_cpp)
    h.scan_symbols()

    print("  [>] Applying v4.7 build-safe patches...")
    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f.endswith(('.c', '.h')):
                h.harmonize_file(os.path.join(root, f), f)

if __name__ == "__main__":
    run_harmonizer()
