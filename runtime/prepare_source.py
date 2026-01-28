import os
import shutil
from pathlib import Path

def setup_build_dir():
    # Define base paths relative to the script location (runtime/..)
    root_dir = Path(__file__).parent.parent
    cpp_dir = root_dir / "Android" / "app" / "src" / "main" / "cpp"

    # Source paths (where the decompiled code lives)
    src_origin = root_dir / "decomp-files" / "src"
    include_origin = root_dir / "decomp-files" / "include"

    # Target paths (where the Android NDK expects them)
    game_src_target = cpp_dir / "game_src"
    include_target = cpp_dir / "include"

    print(f"--- Preparing Source for Build ---")

    # 1. Clean and recreate target directories to ensure a fresh state
    for folder in [game_src_target, include_target]:
        if folder.exists():
            print(f"Cleaning existing directory: {folder}")
            shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(parents=True, exist_ok=True)

    # 2. Copy source files
    if src_origin.exists():
        print(f"Copying source: {src_origin} -> {game_src_target}")
        # dirs_exist_ok=True is safe here because we just cleared the folder
        shutil.copytree(src_origin, game_src_target, dirs_exist_ok=True)
    else:
        print(f"CRITICAL ERROR: Source origin {src_origin} not found!")
        exit(1)

    # 3. Copy headers
    if include_origin.exists():
        print(f"Copying headers: {include_origin} -> {include_target}")
        shutil.copytree(include_origin, include_target, dirs_exist_ok=True)
    else:
        print(f"CRITICAL ERROR: Include origin {include_origin} not found!")
        exit(1)

    print(f"Done! Source synchronized.")

if __name__ == "__main__":
    setup_build_dir()
