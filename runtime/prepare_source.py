import os
import shutil

class SourceHarmonizerV5_2:
    def __init__(self, root_path):
        self.root_path = root_path
        self.ultra_dir = os.path.join(root_path, "ultra")
        self.include_dir = os.path.join(root_path, "include")

    def fix_missing_headers(self):
        """
        Specifically addresses the 'rare_decompression.h' not found error.
        It searches for the file in the project and ensures it's in the 'ultra' 
        directory where 'otr_builder.cpp' expects it.
        """
        target_header = "rare_decompression.h"
        target_path = os.path.join(self.ultra_dir, target_header)
        
        if os.path.exists(target_path):
            print(f"  [>] {target_header} already exists in ultra/.")
            return

        print(f"  [>] Logic Fix: Locating and linking {target_header}...")
        
        # Search the entire root path for the missing header
        found_path = None
        for root, _, files in os.walk(self.root_path):
            if target_header in files:
                found_path = os.path.join(root, target_header)
                break
        
        if found_path:
            shutil.copy2(found_path, target_path)
            print(f"      [!] Successfully copied {target_header} to {self.ultra_dir}")
        else:
            # If not found, create a dummy or search in decomp-files if available
            print(f"      [ERROR] Could not find {target_header} in {self.root_path}")
            # Optional: Add logic to fetch from a known backup directory if needed

def run_v5_2():
    cpp_path = "Android/app/src/main/cpp"
    h = SourceHarmonizerV5_2(cpp_path)
    
    # Apply the fix for the specific 'file not found' error in the log
    h.fix_missing_headers()
    
    print("--- v5.2 Complete: Header path resolution applied ---")

if __name__ == "__main__":
    run_v5_2()
