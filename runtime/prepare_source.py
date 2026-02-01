import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {}
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
        
        # SACRED TYPES: Updated based on the latest log.txt "redefinition" errors.
        self.sacred_types = [
            "sprite", "sfx_e", "ALLink", "ALSound", "N_ALVoice", "ALMicroTime", 
            "Bitmap", "AnSeqElement", "struct5Bs", "struct62s", "struct6Cs",
            "SkeletalAnimation", "SkeletalAnimationCallback"
        ]
        
        # CORE HEADERS: Never modify these to maintain N64 engine integrity.
        self.core_headers = [
            "ultra64.h", "gbi.h", "mbi.h", "sp.h", "libaudio.h", 
            "enums.h", "functions.h", "structs.h", "prop.h"
        ]

    def scan_symbols(self):
        print("  [>] Scanning for structs, enums, and macros...")
        # Expanded patterns to capture the vector/FREE_LIST macros causing log errors
        patterns = [
            r'((?:typedef\s+)?(?:struct|enum)\s*([\w\d_]*)\s*\{[^}]+\}\s*([\w\d_]*)\s*;)',
            r'(typedef\s+[\w\d_]+\s+([\w\d_]+)\s*;)',
            r'(struct\s+([\w\d_]+)\s*;)',
            r'(#define\s+([\w\d_]+)\s*\(.*?\).*)' 
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

        if filename not in self.core_headers:
            # Capture types that the log says are 'unknown'
            type_regex = r'\b(BK[\w\d_]+|[sS][\w\d_]+|ActorMarker|Gfx|Bitmap|FREE_LIST|TUPLE|vector|BoneTransformList)\b'
            potential_types = set(re.findall(type_regex, content))
            needed_defs = []
            
            for type_name in potential_types:
                if type_name in self.symbol_db and type_name not in self.sacred_types:
                    guard = f"_HARM_DEF_{type_name}"
                    if guard not in content:
                        # BRUTE FORCE: Force definition at top of file
                        needed_defs.append(f"#ifndef {guard}\n#define {guard}\n{self.symbol_db[type_name]}\n#endif")

            if needed_defs:
                injection = "\n// --- HARMONIZER v4.9 ---\n" + "\n".join(needed_defs) + "\n"
                # Locate first include or start of file
                match = re.search(r'#include.*?\n', content)
                pos = match.end() if match else 0
                content = content[:pos] + injection + content[pos:]

        if content != orig_content:
            with open(path, 'w') as f: f.write(content)
            return True
        return False

def run_harmonizer():
    android_cpp = "Android/app/src/main/cpp"
    
    # Selective reset: Preserve CMake and Native wrappers
    for sub in ["src", "include"]:
        path = os.path.join(android_cpp, sub)
        if os.path.exists(path): shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)
    
    shutil.copytree("decomp-files/include", os.path.join(android_cpp, "include"), dirs_exist_ok=True)
    shutil.copytree("decomp-files/src", os.path.join(android_cpp, "src"), dirs_exist_ok=True)

    h = SourceHarmonizer(android_cpp)
    h.scan_symbols()

    print("  [>] Applying final v4.9 build patches...")
    patched = 0
    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f.endswith(('.c', '.h')):
                if h.harmonize_file(os.path.join(root, f), f):
                    patched += 1
    print(f"--- Finished: Patched {patched} files ---")

if __name__ == "__main__":
    run_harmonizer()
