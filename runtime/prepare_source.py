import os
import shutil
from pathlib import Path

def setup_build_dir():
    # Define base paths relative to the script location
    root_dir = Path(__file__).parent.parent
    cpp_dir = root_dir / "Android" / "app" / "src" / "main" / "cpp"
    
    # Source paths
    src_origin = root_dir / "decomp-files" / "src"
    include_origin = root_dir / "decomp-files" / "include"

    # Target paths
    game_src_target = cpp_dir / "game_src"
    include_target = cpp_dir / "include"

    print(f"--- Preparing Source for Build ---")

    # Clean and recreate target directories
    for folder in [game_src_target, include_target]:
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)

    # Copy files
    if src_origin.exists():
        print(f"Copying source: {src_origin} -> {game_src_target}")
        shutil.copytree(src_origin, game_src_target, dirs_exist_ok=True)
    
    if include_origin.exists():
        print(f"Copying headers: {include_origin} -> {include_target}")
        shutil.copytree(include_origin, include_target, dirs_exist_ok=True)

    print(f"Done! Source synchronized.")

if __name__ == "__main__":
    setup_build_dir()
