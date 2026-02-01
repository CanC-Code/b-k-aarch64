import os
import shutil
import re

class SourceHarmonizerV5_7:
    def __init__(self, android_path, decomp_path):
        self.android_path = android_path
        self.decomp_path = decomp_path
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

    def fix_conflicting_signatures(self):
        """
        Log Fix: Aligns decompress_rare_asset between C and C++ code.
        The log shows a conflict between 'void' and 's32' returns.
        """
        print("  [>] Logic Fix: Aligning rare_decompression function signatures...")
        target_h = os.path.join(self.ultra_target, "rare_decompression.h")
        if os.path.exists(target_h):
            with open(target_h, 'r') as f: content = f.read()
            # Force the header to use 'void' to match the OTR wrapper implementation
            new_content = content.replace("s32 decompress_rare_asset", "void decompress_rare_asset")
            with open(target_h, 'w') as f: f.write(new_content)
            print("      [!] Forced rare_decompression.h to 'void' return type.")

    def repair_source(self):
        print("  [>] Logic Fix: Repairing legacy C array initializers...")
        patched = 0
        for root, _, files in os.walk(self.src_target):
            for f in files:
                if f.endswith('.c'):
                    path = os.path.join(root, f)
                    with open(path, 'r', errors='ignore') as file: content = file.read()
                    pattern = r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);'
                    if re.search(pattern, content):
                        if '<string.h>' not in content: content = '#include <string.h>\n' + content
                        new_content = re.sub(pattern, r'\1 \2[\3]; memmove(\2, \4, \3);', content)
                        with open(path, 'w') as file: file.write(new_content)
                        patched += 1
        print(f"      [!] Repaired {patched} files.")

    def fix_header_linkage(self):
        target = "rare_decompression.h"
        dest = os.path.join(self.ultra_target, target)
        search_roots = [self.decomp_path, self.android_path, "."]
        for s_root in search_roots:
            for root, _, files in os.walk(s_root):
                if target in files:
                    os.makedirs(self.ultra_target, exist_ok=True)
                    shutil.copy2(os.path.join(root, target), dest)
                    print(f"      [SUCCESS] Linked {target}")
                    return True
        return False

    def run(self):
        print("--- Harmonizer v5.7: Signature Alignment ---")
        self.sync_files()
        self.fix_header_linkage()
        self.fix_conflicting_signatures() # New logic step
        self.repair_source()
        print("--- v5.7 Complete ---")

if __name__ == "__main__":
    ROOT = "Android/app/src/main/cpp"
    DECOMP = "decomp-files"
    if not os.path.exists(DECOMP): DECOMP = "decomp"
    h = SourceHarmonizerV5_7(ROOT, DECOMP)
    h.run()
