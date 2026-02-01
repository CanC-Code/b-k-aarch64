import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {}
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
        # [span_8](start_span)[span_9](start_span)These headers are "Source of Truth" - we NEVER inject into them [cite: 442-459]
        self.source_of_truth = ["functions.h", "structs.h", "model.h", "prop.h", "skeletalanim.h", "enums.h"]

    def scan_symbols(self):
        print("  [>] Brute-force scanning project...")
        # [cite_start]Catching Typedefs, Structs, and Enums[span_8](end_span)[span_9](end_span)
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

        # 1. Update includes for NDK safety
        for old_h, new_h in self.renames.items():
            content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')

        # 2. Strict Injection Control
        # If it's a Source of Truth header, DO NOT inject. [span_10](start_span)This stops the redefinition loops[span_10](end_span).
        if filename not in self.source_of_truth:
            # [span_11](start_span)[span_12](start_span)Find every custom-looking type (BK-prefix, s-prefix, or _t suffix)[span_11](end_span)[span_12](end_span)
            potential_types = set(re.findall(r'\b(BK[\w\d_]+|[sS][\w\d_]+|ActorMarker|BoneTransformList|Gfx)\b', content))
            needed_defs = []
            
            for type_name in potential_types:
                if type_name in self.symbol_db:
                    # BRUTE FORCE: Wrap in unique guards so even if it exists elsewhere, it won't crash
                    guard = f"_FORCE_DEF_{type_name}"
                    needed_defs.append(f"#ifndef {guard}\n#define {guard}\n{self.symbol_db[type_name]}\n#endif")

            if needed_defs:
                injection = "\n// --- BRUTE FORCE HARMONIZER v4.1 ---\n" + "\n".join(needed_defs) + "\n"
                # Inject after includes to ensure it doesn't conflict with system headers
                match = re.search(r'#include.*?\n', content)
                pos = match.end() if match else 0
                content = content[:pos] + injection + content[pos:]

        if content != orig_content:
            with open(path, 'w') as f: f.write(content)
            return True
        return False

def prepare_source():
    android_cpp = "Android/app/src/main/cpp"
    # Sync folders
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
