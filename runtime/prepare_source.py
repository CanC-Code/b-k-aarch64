import os
import shutil
import re

class SourceHarmonizer:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {}
        # Avoid NDK collisions with standard headers
        self.renames = {"string.h": "game_string.h", "time.h": "game_time.h", "sched.h": "game_sched.h"}
        # [span_3](start_span)[span_4](start_span)List of types already heavily defined in core headers to skip injection [cite: 570-587]
        self.blacklist = [
            "BKVtxRef", "BKMesh", "BKGeoList", "BKMeshList", "BKVertexList", 
            "BKCollisionGeo", "BKCollisionTri", "BKCollisionList", "BKEffectsList",
            "sprite", "sfx_e", "OSMesg", "OSThread", "OSTask"
        ]

    def scan_symbols(self):
        print("  [>] Scanning for global types...")
        # [cite_start]Patterns for structs, enums, and BK-specific typedefs [cite: 560-569]
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
                                # Only store if not blacklisted and not already present
                                if name and name not in self.symbol_db and name not in self.blacklist:
                                    self.symbol_db[name] = full_def

    def rename_physical_headers(self):
        for root, _, files in os.walk(self.root_path):
            for filename in files:
                if filename in self.renames:
                    old_path = os.path.join(root, filename)
                    new_path = os.path.join(root, self.renames[filename])
                    if not os.path.exists(new_path): os.rename(old_path, new_path)

    def harmonize_file(self, path, filename):
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
        orig_content = content

        # Update include paths for renamed headers
        for old_h, new_h in self.renames.items():
            content = content.replace(f'#include <{old_h}>', f'#include "{new_h}"')
            content = content.replace(f'#include "{old_h}"', f'#include "{new_h}"')

        # [cite_start]Skip core headers that are the source of most definitions[span_3](end_span)[span_4](end_span)
        is_core = any(x in filename for x in ["ultra64.h", "gbi.h", "mbi.h", "structs.h", "model.h", "enums.h"])
        
        if not is_core:
            # [span_5](start_span)[span_6](start_span)Match any word that looks like a custom type or BK struct [cite: 567-569]
            potential_types = set(re.findall(r'\b(BK[\w\d_]+|[sS][\w\d_]+|ActorMarker|Gfx)\b', content))
            needed_defs = []
            for type_name in potential_types:
                if type_name in self.symbol_db and type_name not in self.blacklist:
                    # BRUTE FORCE: Only inject if the definition is physically missing
                    if f"struct {type_name}" not in content and f"typedef struct {type_name}" not in content:
                        guard = f"_GUARD_{type_name}"
                        needed_defs.append(f"#ifndef {guard}\n#define {guard}\n{self.symbol_db[type_name]}\n#endif")
            
            # Auto-generate prototypes for static functions to fix declaration errors
            static_funcs = re.findall(r'^static\s+[\w\*]+\s+([\w\d_]+)\s*\(', content, re.MULTILINE)
            prototypes = []
            for f in static_funcs:
                sig = re.search(r'^(static\s+[\w\*]+\s+' + re.escape(f) + r'\s*\([^)]*\))', content, re.MULTILINE)
                if sig: prototypes.append(f"{sig.group(1)};")

            if needed_defs or prototypes:
                injection = "\n// --- HARMONIZER v4.0 ---\n" + "\n".join(needed_defs + prototypes) + "\n"
                match = re.search(r'#include.*?\n', content)
                pos = match.end() if match else 0
                content = content[:pos] + injection + content[pos:]

        if content != orig_content:
            with open(path, 'w') as f: f.write(content)
            return True
        return False

def prepare_source():
    android_cpp = "Android/app/src/main/cpp"
    # Selective wipe to protect your CMake and Wrapper files
    for sub in ["src", "include"]:
        target = os.path.join(android_cpp, sub)
        if os.path.exists(target): shutil.rmtree(target)
        os.makedirs(target, exist_ok=True)

    shutil.copytree("decomp-files/include", os.path.join(android_cpp, "include"), dirs_exist_ok=True)
    shutil.copytree("decomp-files/src", os.path.join(android_cpp, "src"), dirs_exist_ok=True)

    harmonizer = SourceHarmonizer(android_cpp)
    harmonizer.rename_physical_headers()
    harmonizer.scan_symbols()

    patched = 0
    for root, _, files in os.walk(android_cpp):
        for f in files:
            if f.endswith(('.c', '.h')):
                if harmonizer.harmonize_file(os.path.join(root, f), f): patched += 1
    print(f"--- Finished: Patched {patched} files ---")

if __name__ == "__main__":
    prepare_source()
