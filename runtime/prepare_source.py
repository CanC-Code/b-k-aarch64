#!/usr/bin/env python3
"""
SourceHarmonizer v75.67
BK AArch64 Android port — IDO/N64 decomp source → Clang/NDK compatibility

Fixing 'conflicting types' by implementing automatic function prototyping.
"""

import re
from pathlib import Path

# --- GLOBAL CONFIGURATION ---
PREAMBLE_MARKER = "/* SH-v75.67-DSI */"
PREAMBLE_TEMPLATE = """\
{marker}
#ifndef _SH_TYPES_GUARD_
#define _SH_TYPES_GUARD_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// Direct N64/IDO Type Mapping
typedef uint8_t   u8;
typedef int8_t    s8;
typedef uint16_t  u16;
typedef int16_t   s16;
typedef uint32_t  u32;
typedef int32_t   s32;
typedef uint64_t  u64;
typedef int64_t   s64;
typedef float     f32;
typedef double    f64;

#ifndef F3DEX_GBI_2
#define F3DEX_GBI_2
#endif

// Block legacy bool redefinitions
#define _BOOL_H_
#define __bool_true_false_are_defined 1

// --- AUTO-GENERATED PROTOTYPES ---
{prototypes}
// ---------------------------------
#endif
"""

# ─────────────────────────────────────────────────────────────────────────────
# PROTOTYPE EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_local_prototypes(content):
    """
    Scans the file for function definitions and returns a string of 
    forward declarations to prevent 'implicit declaration' errors.
    """
    # Pattern looks for: [Type] [FunctionName]( [Args] ) {
    # It excludes lines ending in ; (declarations) or starting with # (macros)
    func_pattern = r'^(\w+\s+\*?\w+)\(([^;]*?)\)\s*\{'
    matches = re.finditer(func_pattern, content, re.MULTILINE)
    
    protos = []
    for m in matches:
        return_type_and_name = m.group(1)
        args = m.group(2).strip()
        # Clean up whitespace and form a prototype
        proto = f"extern {return_type_and_name}({args});"
        if proto not in protos:
            protos.append(proto)
            
    return "\n".join(protos)

# ─────────────────────────────────────────────────────────────────────────────
# CORE REPAIR LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def process_c_file(path: Path):
    original = path.read_text(encoding='utf-8', errors='ignore')
    
    # 1. Clean up ALL previous Harmonizer blocks (all versions)
    content = re.sub(r'/\* SH-v75\..*? \*/.*?#endif\n', '', original, flags=re.DOTALL)
    
    # 2. Extract current function signatures from the cleaned content
    prototypes = extract_local_prototypes(content)
    
    # 3. Build the new Preamble with version-specific prototypes
    final_preamble = PREAMBLE_TEMPLATE.format(
        marker=PREAMBLE_MARKER,
        prototypes=prototypes
    )
    
    # 4. Apply 64-bit pointer fixes
    content = final_preamble + content
    content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)
    
    if content != original:
        path.write_text(content, encoding='utf-8')
        return True
    return False

def main():
    repo_root = Path(__file__).resolve().parent.parent
    src_dir = repo_root / "decomp-files" / "src"

    print(f"[>] SourceHarmonizer v75.67: Prototype Extraction Mode")
    
    # Ensure bool.h is still neutralized from v75.66
    bool_h = repo_root / "decomp-files" / "include" / "bool.h"
    if bool_h.exists():
        bool_h.write_text("/* SH-v75.67 */\n#include <stdbool.h>\n", encoding='utf-8')

    modified_count = 0
    if src_dir.exists():
        for path in sorted(src_dir.rglob("*.c")):
            if process_c_file(path):
                modified_count += 1
                
    print(f"[+] Done. Processed {modified_count} source files with auto-prototyping.")

if __name__ == "__main__":
    main()
