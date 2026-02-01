import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {}
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
        # [span_11](start_span)High-traffic types that cause redefinition loops in your log [cite: 11-28]
        self.sacred_types = ["BKModel", "BKVertexList", "Struct62s", "Struct6Cs", "SkeletalAnimation", "SkeletalAnimationCallback", "sprite_prop_s", "SpriteProp"]

    def scan_symbols(self):
        print("  [>] Brute-force scanning for all project types...")
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

        # [cite_start]Core engine headers shouldn't receive injections to prevent loops[span_11](end_span)
        is_core = any(x in filename for x in ["functions.h", "structs.h", "prop.h", "ultra64.h", "gbi.h"])
        
        if not is_core:
            # [span_12](start_span)[span_13](start_span)Capture custom types and types found missing in log (BoneTransformList, StopNSwop_Data)[span_12](end_span)[span_13](end_span)
            potential_types = set(re.findall(r'\b(BK[\w\d_]+|[sS][\w\d_]+|ActorMarker|Gfx|BoneTransformList|StopNSwop_Data)\b', content))
            needed_defs = []
            
            for type_name in potential_types:
                if type_name in self.symbol_db and type_name not in self.sacred_types:
                    # BRUTE FORCE: Use a unique guard for every single type
                    guard = f"_FORCE_DEF_{type_name}"
                    if guard not in content:
                        needed_defs.append(f"#ifndef {guard}\n#define {guard}\n{self.symbol_db[type_name]}\n#endif")

            if needed_defs:
                injection = "\n// --- HARMONIZER v4.6 ---\n" + "\n".join(needed_defs) + "\n"
                match = re.search(r'#include.*?\n', content)
                pos = match.end() if match else 0
                content = content[:pos] + injection + content[pos:]

        if content != orig_content:
            with open(path, 'w') as f: f.write(content)
            return True
        return False

def prepare_source():
    android_cpp = "Android/app/src/main/cpp"
    # Selective wipe: ONLY clean src/include, preserve CMake/Bridge files
    for sub in ["src", "include"]:
        target = os.path.join(android_cpp, sub)
        if os.path.exists(target): shutil.rmtree(target)
        os.makedirs(target, exist_ok=True)

    shutil.copytree("decomp-files/include", os.path.join(android_cpp, "include"), dirs_exist_ok=True)
    shutil.copytree("decomp-files/src", os.path.join(android_cpp, "src"), dirs_exist_ok=True)

    harmonizer = SourceHarmonizer(android_cpp)
    harmonizer.scan_symbols()

    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f.endswith(('.c', '.h')):
                harmonizer.harmonize_file(os.path.join(root, f), f)

if __name__ == "__main__":
    prepare_source()
