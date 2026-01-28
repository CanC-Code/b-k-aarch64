import os
import shutil
import sys
from pathlib import Path

def patch_file(file_path, patch_map):
    """Replaces strings in a file based on a dictionary map."""
    if not file_path.exists():
        print(f"  [!] Missing for patch: {file_path.name}")
        return

    content = file_path.read_text(encoding='utf-8')
    original_content = content
    for search, replace in patch_map.items():
        content = content.replace(search, replace)

    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"  [✓] Patched: {file_path.name}")

def inject_cpp_fixes(file_path):
    """Injects standard headers and wraps legacy headers in extern C blocks."""
    if not file_path.exists():
        print(f"  [!] Target not found for injection: {file_path.name}")
        return

    lines = file_path.read_text(encoding='utf-8').splitlines()

    # Avoid double-patching
    if any('extern "C" {' in line for line in lines[:30]):
        print(f"  [-] Already guarded: {file_path.name}")
        return

    # Start with mandatory C++ fixes for Android
    new_content = ["#include <sched.h> // Fixed: sched_yield\n", "#include <stddef.h>\n", "#include <stdint.h>\n"]

    for line in lines:
        # Wrap N64-specific headers to prevent C++ name mangling conflicts
        if any(x in line for x in ["2.0L", "ultratypes.h", "gbi.h", "os.h"]) and "#include" in line:
            new_content.append('extern "C" {\n')
            new_content.append(line + "\n")
            new_content.append('}\n')
        else:
            new_content.append(line + "\n")

    file_path.write_text("".join(new_content), encoding='utf-8')
    print(f"  [✓] Injected C++ guards: {file_path.name}")

def setup_build_dir():
    # LOCATE DIRECTORIES
    # Script is in /runtime/, so .parent is /runtime/, .parent.parent is root
    script_dir = Path(__file__).parent.resolve()
    root_dir = script_dir.parent
    
    # Destination in Android project
    cpp_root = root_dir / "Android" / "app" / "src" / "main" / "cpp"
    
    # Source origins (Adjust these names if your decomp folders are named differently)
    src_origin = root_dir / "src"
    include_origin = root_dir / "include"

    print(f"--- Environment Debug ---")
    print(f"Root Directory: {root_dir}")
    print(f"Target CPP Root: {cpp_root}")

    # 1. SYNCHRONIZE FILES (The 'Lost Logic')
    print(f"--- Synchronizing Source Files ---")
    
    mapping = [
        (src_origin, cpp_root / "game_src"),
        (include_origin, cpp_root / "include")
    ]

    for source, target in mapping:
        if source.exists():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(source, target, dirs_exist_ok=True)
            print(f"  [→] Synchronized: {source.name} -> {target.name}")
        else:
            print(f"  [!] CRITICAL: Source {source} not found! Check repository structure.")
            # We don't exit yet to see if other parts exist, but build will likely fail.

    # 2. APPLY COMPATIBILITY PATCHES
    print(f"--- Applying Android/ARM64 Patches ---")

    # Fix A: Fix sprintf linkage in the N64 OS header
    os_libc = cpp_root / "include" / "2.0L" / "PR" / "os_libc.h"
    patch_file(os_libc, {
        'extern int              sprintf(char *s, const char *fmt, ...);': 
        '#ifdef __cplusplus\nextern "C" {\n#endif\nextern int sprintf(char *s, const char *fmt, ...);\n#ifdef __cplusplus\n}\n#endif'
    })

    # Fix B: Fix ultratypes.h for 64-bit Android (long is 64-bit on ARM64, we need 32-bit)
    ultratypes = cpp_root / "include" / "2.0L" / "PR" / "ultratypes.h"
    patch_file(ultratypes, {
        "typedef unsigned long       u32;": "typedef unsigned int u32;",
        "typedef signed long         s32;": "typedef signed int s32;",
        "typedef int bool;": "#ifndef __cplusplus\ntypedef int bool;\n#endif"
    })

    # Fix C: Inject guards into wrapper files
    cpp_targets = [
        cpp_root / "emulator" / "stubs.cpp",
        cpp_root / "emulator" / "resource_mgr.cpp",
        cpp_root / "ultra" / "NativeBridge.cpp"
    ]
    for target in cpp_targets:
        inject_cpp_fixes(target)

    # Fix D: Handle Shadow Headers (Standard Library conflicts)
    shadow_headers = [
        (cpp_root / "include" / "string.h", cpp_root / "include" / "game_string.h"),
        (cpp_root / "include" / "time.h", cpp_root / "include" / "game_time.h")
    ]
    for old_path, new_path in shadow_headers:
        if old_path.exists():
            if new_path.exists():
                os.remove(old_path)
            else:
                old_path.rename(new_path)
            print(f"  [✓] Resolved Shadow Header: {old_path.name}")

    print("--- Preparation Complete ---")

if __name__ == "__main__":
    setup_build_dir()
