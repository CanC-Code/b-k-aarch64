import os
import shutil
import re

class SourceHarmonizerV5_5:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
        
        # Target directories in Android project
        self.src_target = os.path.join(android_path, "src")
        self.include_target = os.path.join(android_path, "include")
        self.ultra_target = os.path.join(android_path, "ultra")

    def sync_files(self):
        """Physically copies the decompiled source into the Android project."""
        print(f"  [>] Syncing source from {self.decomp_path}...")
        
        # Map source to target
        mappings = {
            "src": self.src_target,
            "include": self.include_target
        }

        for sub, target in mappings.items():
            source = os.path.join(self.decomp_path, sub)
            if os.path.exists(source):
                # Clean target first to ensure a fresh sync
                if os.path.exists(target): shutil.rmtree(target)
                shutil.copytree(source, target)
                count = len([f for _, _, files in os.walk(target) for f in files])
                print(f"      [+] Synced {count} files to {sub}/")
            else:
                print(f"      [!] Warning: Source {source} not found!")

    def repair_source(self):
        """Fixes legacy array initializer syntax errors in the newly synced files."""
        print("  [>] Logic Fix: Repairing legacy C array initializers...")
        patched = 0
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file:
                        content = file.read()
                    
                    # Fix: u8 arr[N] = SYMBOL; -> u8 arr[N]; memmove(arr, SYMBOL, N);
                    pattern = r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);'
                    new_content = re.sub(pattern, r'\1 \2[\3]; memmove(\2, \4, \3);', content)
                    
                    if new_content != content:
                        if '#include <string.h>' not in new_content:
                            new_content = '#include <string.h>\n' + new_content
                        with open(path, 'w') as file:
                            file.write(new_content)
                        patched += 1
        print(f"      [!] Repaired {patched} files.")

    def fix_header_linkage(self):
        """Ensures rare_decompression.h is reachable by the builder."""
        target = "rare_decompression.h"
        dest = os.path.join(self.ultra_target, target)
        
        if not os.path.exists(dest):
            # Search freshly synced include folder
            for root, _, files in os.walk(self.include_target):
                if target in files:
                    shutil.copy2(os.path.join(root, target), dest)
                    print(f"      [!] Linked {target} to ultra/ folder.")
                    return
            print(f"      [!] Error: Could not find {target} to link!")

    def run(self):
        print("--- Harmonizer v5.5: Full Sync & Repair ---")
        self.sync_files()
        self.repair_source()
        self.fix_header_linkage()
        print("--- v5.5 Complete: Source is synchronized and patched ---")

if __name__ == "__main__":
    # Settings for your specific environment
    ANDROID_CPP_ROOT = "Android/app/src/main/cpp"
    DECOMP_SOURCE = "decomp-files" # Ensure this folder contains your 'src' and 'include'
    
    # Fallback for different environments
    if not os.path.exists(DECOMP_SOURCE):
        DECOMP_SOURCE = "decomp" 

    h = SourceHarmonizerV5_5(ANDROID_CPP_ROOT, DECOMP_SOURCE)
    h.run()
