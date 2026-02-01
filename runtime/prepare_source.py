import os
import shutil
import re

class SourceHarmonizerV5_6:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        
        # Target directories in Android project
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.ultra_target = os.path.join(android_path, "ultra")

    def sync_files(self):
        print(f"  [>] Syncing source from {self.decomp_path}...")
        mappings = {"src": self.src_target, "include": self.include_target}
        for sub, target in mappings.items():
            source = os.path.join(self.decomp_path, sub)
            if os.path.exists(source):
                if os.path.exists(target): shutil.rmtree(target)
                shutil.copytree(source, target)
                print(f"      [+] Synced {sub}/ folder.")

    def repair_source(self):
        """Fixes legacy array initializer syntax and ensures string.h for memmove."""
        print("  [>] Logic Fix: Repairing legacy C array initializers...")
        patched = 0
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                    
                    # Pattern for: u8 arr[size] = symbol;
                    pattern = r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);'
                    if re.search(pattern, content):
                        # Ensure string.h is present for memmove
                        if '<string.h>' not in content and '"string.h"' not in content:
                            content = '#include <string.h>\n' + content
                        
                        new_content = re.sub(pattern, r'\1 \2[\3]; memmove(\2, \4, \3);', content)
                        with open(path, 'w') as file:
                            file.write(new_content)
                        patched += 1
        print(f"      [!] Repaired {patched} files.")

    def fix_header_linkage(self):
        """Deep search for rare_decompression.h to fix the Ninja fatal error."""
        target = "rare_decompression.h"
        dest = os.path.join(self.ultra_target, target)
        
        print(f"  [>] Searching for {target}...")
        # Broad search: Check decomp_path, include_target, and the root
        search_roots = [self.decomp_path, self.android_path, "."]
        
        for s_root in search_roots:
            for root, _, files in os.walk(s_root):
                if target in files:
                    found_path = os.path.join(root, target)
                    os.makedirs(self.ultra_target, exist_ok=True)
                    shutil.copy2(found_path, dest)
                    print(f"      [SUCCESS] Linked {target} from {root}")
                    return True
        
        print(f"      [ERROR] {target} NOT FOUND. Ninja will fail.")
        return False

    def run(self):
        print("--- Harmonizer v5.6: Deep Search & Repair ---")
        self.sync_files()
        self.repair_source()
        self.fix_header_linkage()
        print("--- v5.6 Complete ---")

if __name__ == "__main__":
    # Standard GitHub Actions / Android Project Paths
    ROOT = "Android/app/src/main/cpp"
    DECOMP = "decomp-files"
    
    # Fallback for manual runs
    if not os.path.exists(DECOMP): DECOMP = "decomp"

    h = SourceHarmonizerV5_6(ROOT, DECOMP)
    h.run()
