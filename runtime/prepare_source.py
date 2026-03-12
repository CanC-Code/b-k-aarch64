#!/usr/bin/env python3
import re
from pathlib import Path

# --- CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-v80.1-AUTOMORPH */"

def unique_struct_fix(match):
    """
    Callback for re.sub to provide unique tags for anonymous structs.
    """
    if not hasattr(unique_struct_fix, "counter"):
        unique_struct_fix.counter = 0
    unique_struct_fix.counter += 1
    
    struct_body = match.group(1)
    typename = match.group(2)
    tag = f"_SH_TAG_{unique_struct_fix.counter}"
    
    # Converts: typedef struct { ... } Typename;
    # To: typedef struct tag { ... } Typename;
    return f"typedef struct {tag} {{ {struct_body} }} {typename};"

def deep_clean_sdk(decomp_root: Path):
    """
    Physically repairs legacy SDK headers to work with modern Clang.
    """
    # 1. Neutralize bool.h
    bool_h = decomp_root / "include" / "bool.h"
    if bool_h.exists():
        bool_h.write_text("#include <stdbool.h>\n", encoding='utf-8')
        print("  [FIXED] bool.h redirected to stdbool.h")

    audio_headers = [
        decomp_root / "include/2.0L/PR/libaudio.h",
        decomp_root / "include/2.0L/PR/n_libaudio.h",
        decomp_root / "include/synthInternals.h"
    ]
    
    for h_path in audio_headers:
        if not h_path.exists(): continue
        content = h_path.read_text(encoding='utf-8', errors='ignore')
        
        # Reset counter for each file to keep it clean
        unique_struct_fix.counter = 0
        
        # 2. Fix Anonymous Typedefs
        # This pattern captures the body and the trailing typename
        content = re.sub(r'typedef\s+struct\s*\{(.*?)\}\s*(\w+);', unique_struct_fix, content, flags=re.DOTALL)
        
        # 3. Fix the specific ALFilter/ALAuxBus redefinition traps
        # Legacy SDKs often do 'typedef struct { ... } ALFilter;' AND 'struct ALFilter_s;'
        content = content.replace("struct ALFilter_s", "struct ALFilter")
        content = content.replace("struct ALAuxBus_s", "struct ALAuxBus")
        
        h_path.write_text(content, encoding='utf-8')
        print(f[FIXED] {h_path.name} normalized with unique tags.")

# ... (keep your synthesize_preamble and process_file functions as they were) ...

def apply_source_fixes(content):
    # Fix 64-bit Pointer Truncation
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    content = re.sub(r'\(u32\)\s*\((.*?)\)', r'(u32)(uintptr_t)(\1)', content)
    
    # Remove manual declarations that often conflict with repaired headers
    clash_patterns = [
        r'struct\s+ALCSPlayer;', r'typedef\s+struct\s+ALCSPlayer\s+ALCSPlayer;',
        r'struct\s+N_ALCSPlayer;', r'typedef\s+struct\s+N_ALCSPlayer\s+N_ALCSPlayer;'
    ]
    for pattern in clash_patterns:
        content = re.sub(pattern, '', content)
        
    return content

# (Ensure main() calls the updated functions)
