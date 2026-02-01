import os
import shutil
import re

class SourceHarmonizerV5_4:
    def __init__(self, root_path):
        self.root_path = root_path
        # Core source directories derived from project structure
        self.src_dir = os.path.join(root_path, "src")
        self.ultra_dir = os.path.join(root_path, "ultra")
        self.include_dir = os.path.join(root_path, "include")

    def ensure_directories_exist(self):
        """Validates that the source folders are actually present."""
        found_any = False
        for d in [self.src_dir, self.ultra_dir, self.include_dir]:
            if os.path.exists(d):
                count = len([f for f in os.listdir(d) if f.endswith(('.c', '.h', '.cpp'))])
                print(f"  [>] Verified: {os.path.basename(d)}/ folder found with {count} files.")
                if count > 0: found_any = True
            else:
                print(f"  [!] Missing Critical Directory: {d}")
        return found_any

    def repair_array_logic(self):
        """Fixes the u8 array initializer syntax errors found in previous logs."""
        print("  [>] Logic Fix: Repairing legacy C array initializers in all .c files...")
        count = 0
        for root, _, files in os.walk(self.src_dir):
            for filename in files:
                if filename.endswith('.c'):
                    path = os.path.join(root, filename)
                    with open(path, 'r', errors='ignore') as f: content = f.read()
                    
                    pattern = r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);'
                    new_content = re.sub(pattern, r'\1 \2[\3]; memmove(\2, \4, \3);', content)
                    
                    if new_content != content:
                        if '#include <string.h>' not in new_content:
                            new_content = '#include <string.h>\n' + new_content
                        with open(path, 'w') as f: f.write(new_content)
                        count += 1
        print(f"      [!] Repaired {count} array assignments.")

    def run_full_repair(self):
        print("--- Harmonizer v5.4: Universal Source Repair ---")
        
        if not self.ensure_directories_exist():
            print("  [ERROR] No source files found to repair. Check your project structure.")
            return

        self.repair_array_logic()
        
        # Resolve the specific rare_decompression.h issue
        target_h = "rare_decompression.h"
        target_dest = os.path.join(self.ultra_dir, target_h)
        if not os.path.exists(target_dest):
            for root, _, files in os.walk(self.root_path):
                if target_h in files:
                    shutil.copy2(os.path.join(root, target_h), target_dest)
                    print(f"      [!] Linked {target_h} to ultra/ folder.")
                    break

        print("--- v5.4 Complete: Source is ready for CMake linking ---")

def run():
    # Use a relative path that works within the GitHub Actions runner environment
    base_path = "Android/app/src/main/cpp"
    if not os.path.exists(base_path):
        # Fallback if running from a different directory
        base_path = "."
        
    h = SourceHarmonizerV5_4(base_path)
    h.run_full_repair()

if __name__ == "__main__":
    run()
