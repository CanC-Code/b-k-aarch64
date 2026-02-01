import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {}
        # NDK safety renames
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
        
        # SACRED TYPES: These are already defined correctly in core headers. 
        # Adding them here prevents the "typedef redefinition" errors found in log.txt.
        self.sacred_types = [
            "BKVertexList", "BKAnimationList", "BKTextureList", "BKModelBin", 
            "BKGfxList", "BKModel", "Struct84s", "struct5Bs", "sfx_e", "sprite",
            "ALLink", "ALSound", "N_ALVoice", "ALMicroTime", "Bitmap", "Gfx"
        ]
        
        # [span_3](start_span)[span_4](start_span)CORE HEADERS: Do not inject anything into these to prevent loops [cite: 401-423]
        self.core_headers = [
            "ultra64.h", "gbi.h", "mbi.h", "sp.h", "libaudio.h", 
            "model.h", "structs.h", "enums.h", "functions.h"
        ]

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

        # Rename colliding headers
        for old_h, new_h in self.renames.items():
            content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')

        # [cite_start]Logic: Only inject into non-core files to avoid the redefinition errors in log[span_3](end_span)[span_4](end_span)
        if filename not in self.core_headers:
            # Find every possible custom type usage
            potential_types = set(re.findall(r'\b(BK[\w\d_]+|[sS][\w\d_]+|ActorMarker|Gfx|Bitmap|AL[\w\d_]+)\b', content))
            needed_defs = []
            
            for type_name in potential_types:
                # If we have a definition and it's NOT a sacred type that causes crashes
                if type_name in self.symbol_db and type_name not in self.sacred_types:
                    # BRUTE FORCE: Wrap in unique guards
                    guard = f"_HARM_DEF_{type_name}"
                    if guard not in content:
                        needed_defs.append(f"#ifndef {guard}\n#define {guard}\n{self.symbol_db[type_name]}\n#endif")

            if needed_defs:
                injection = "\n// --- HARMONIZER v4.5 ---\n" + "\n".join(needed_defs) + "\n"
                # Insert after the first include to ensure system types are loaded first
                match = re.search(r'#include.*?\n', content)
                pos = match.end() if match else 0
                content = content[:pos] + injection + content[pos:]

        if content != orig_content:
            with open(path, 'w') as f: f.write(content)
            return True
        return False

def run_harmonizer():
    target_dir = "Android/app/src/main/cpp"
    
    # Reset and Sync
    for sub in ["src", "include"]:
        path = os.path.join(target_dir, sub)
        if os.path.exists(path): shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)
    
    shutil.copytree("decomp-files/include", os.path.join(target_dir, "include"), dirs_exist_ok=True)
    shutil.copytree("decomp-files/src", os.path.join(target_dir, "src"), dirs_exist_ok=True)

    h = SourceHarmonizer(target_dir)
    h.scan_symbols()

    print("  [>] Applying v4.5 conflict resolution...")
    for root, _, files in os.walk(target_dir):
        for f in files:
            if f.endswith(('.c', '.h')):
                h.harmonize_file(os.path.join(root, f), f)
    print("  [!] Done. Ready for build.")

if __name__ == "__main__":
    run_harmonizer()
