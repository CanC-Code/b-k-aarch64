import os
import shutil
import re

class SourceHarmonizerV5_1:
    def __init__(self, root_path):
        self.root_path = root_path
        # We'll use this to fix the specific array initializer error in leafboat.c
        self.src_dir = os.path.join(root_path, "src")

    def fix_array_initializers(self):
        """
        Finds 'u8 arr[N] = SYMBOL;' and converts it to:
        u8 arr[N]; memmove(arr, SYMBOL, N);
        [span_5](start_span)This fixes the 'array initializer must be an initializer list' error[span_5](end_span).
        """
        print("  [>] Logic Fix: Repairing modern C array initializers...")
        for root, _, files in os.walk(self.src_dir):
            for filename in files:
                if filename.endswith('.c'):
                    path = os.path.join(root, filename)
                    with open(path, 'r', errors='ignore') as f:
                        content = f.read()
                    
                    # Regex to find: type name[size] = symbol;
                    # Capture: 1=type, 2=name, 3=size, 4=symbol
                    pattern = r'(\w+)\s+(\w+)\[(\d+)\]\s*=\s*([^;{]+);'
                    new_content = re.sub(
                        pattern, 
                        r'\1 \2[\3]; memmove(\2, \4, \3);', 
                        content
                    )
                    
                    if new_content != content:
                        # Ensure string.h is included for memmove
                        if '#include <string.h>' not in new_content and '#include "game_string.h"' not in new_content:
                            new_content = '#include <string.h>\n' + new_content
                        
                        with open(path, 'w') as f:
                            f.write(new_content)
                            print(f"      [!] Repaired array assignment in {filename}")

def run_v5_1():
    cpp_path = "Android/app/src/main/cpp"
    # Note: We assume the previous V5 logic has already refreshed/deduplicated files
    h = SourceHarmonizerV5_1(cpp_path)
    
    # [span_6](start_span)[span_7](start_span)Apply the specific syntactic fix for the current log error[span_6](end_span)[span_7](end_span)
    h.fix_array_initializers()
    
    print("--- v5.1 Complete: Syntactic array fixes applied ---")

if __name__ == "__main__":
    run_v5_1()
