import os
import shutil
import re

class SourceHarmonizerV5:
    def __init__(self, root_path):
        self.root_path = root_path
        self.symbol_db = {}
        # Core headers that MUST NOT be modified by injection
        self.protected_dir = os.path.join(root_path, "include")

    def fix_model_h(self):
        """Specifically targets the massive redefinitions in model.h revealed in log."""
        model_h_path = os.path.join(self.protected_dir, "model.h")
        if not os.path.exists(model_h_path): return
        
        print("  [>] Log Fix: Deduplicating model.h structures...")
        with open(model_h_path, 'r') as f: content = f.read()
        
        # [span_6](start_span)Types identified in log as redefined [cite: 16-37]
        redefined_types = [
            "BKVtxRef", "BKMesh", "BKGeoList", "BKMeshList", "BKVertexList", 
            "BKCollisionGeo", "BKCollisionTri", "BKCollisionList", "BKEffectsList", 
            "BKAnimation", "BKAnimationList"
        ]
        
        for t in redefined_types:
            # Matches the second occurrence of a typedef struct for these types
            pattern = r'(typedef\s+struct.*?}\s*' + t + r'\s*;)'
            matches = list(re.finditer(pattern, content, re.DOTALL))
            if len(matches) > 1:
                # Keep the first, comment out the rest
                for m in matches[1:]:
                    content = content[:m.start()] + "/* Redundant: " + m.group(1) + " */" + content[m.end():]
        
        with open(model_h_path, 'w') as f: f.write(content)

    def scan_symbols(self):
        print("  [>] Scanning for type names...")
        # We only need the name now for forward declarations
        pattern = r'(?:struct|enum)\s+([\w\d_]+)\s*\{'
        for root, _, files in os.walk(self.root_path):
            for filename in files:
                if filename.endswith(('.c', '.h')):
                    with open(os.path.join(root, filename), 'r', errors='ignore') as f:
                        for name in re.findall(pattern, f.read()):
                            self.symbol_db[name] = True

    def harmonize_c_file(self, path):
        """Injects only FORWARD DECLARATIONS to avoid redefinition errors."""
        with open(path, 'r', errors='ignore') as f: content = f.read()
        orig = content
        
        # [cite_start]Identify types used but potentially undefined[span_6](end_span)
        potential_types = set(re.findall(r'\b(BK[\w\d_]+|struct\s+[\w\d_]+)\b', content))
        injections = []
        
        for t in potential_types:
            clean_name = t.replace("struct ", "")
            if clean_name in self.symbol_db:
                guard = f"_FWD_{clean_name}"
                if guard not in content:
                    injections.append(f"#ifndef {guard}\n#define {guard}\nstruct {clean_name};\ntypedef struct {clean_name} {clean_name};\n#endif")

        if injections:
            content = "// --- HARMONIZER v5.0 ---\n" + "\n".join(injections) + "\n" + content
            with open(path, 'w') as f: f.write(content)

def run_v5():
    cpp_path = "Android/app/src/main/cpp"
    h = SourceHarmonizerV5(cpp_path)
    
    # 1. Physical file preparation (Standard Refresh)
    for s in ["src", "include"]:
        p = os.path.join(cpp_path, s)
        if os.path.exists(p): shutil.rmtree(p)
        shutil.copytree(f"decomp-files/{s}", p)

    # 2. Logic Phase: Fix the source of the redefinitions
    h.fix_model_h()
    h.scan_symbols()

    # 3. [span_7](start_span)Application Phase: Patch ONLY .c files to avoid header pollution[span_7](end_span)
    for root, _, files in os.walk(os.path.join(cpp_path, "src")):
        for f in files:
            if f.endswith('.c'):
                h.harmonize_c_file(os.path.join(root, f))
    print("--- v5.0 Complete: Logic-based patches applied ---")

if __name__ == "__main__":
    run_v5()
