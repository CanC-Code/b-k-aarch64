import os
import sys
import subprocess

def run_magick(args):
    """Try calling 'magick' (v7+) then 'convert' (v6) fallback."""
    try:
        subprocess.run(["magick"] + args, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        subprocess.run(["convert"] + args, check=True)

def generate_icons(source_path):
    # Android icon sizes for mdpi, hdpi, xhdpi, xxhdpi, xxxhdpi
    icon_specs = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192
    }

    res_dir = "Android/app/src/main/res"

    if not os.path.exists(source_path):
        print(f"Error: Source file {source_path} not found.")
        return

    for folder, size in icon_specs.items():
        target_dir = os.path.join(res_dir, folder)
        os.makedirs(target_dir, exist_ok=True)

        # Standard ic_launcher.png
        standard_path = os.path.join(target_dir, "ic_launcher.png")
        run_magick([
            source_path,
            "-gravity", "center", 
            "-extent", "%[fx:w<h?w:h]x%[fx:w<h?w:h]", # Force square
            "-resize", f"{size}x{size}",
            "-unsharp", "0x1",
            standard_path
        ])

        # Round ic_launcher_round.png
        round_path = os.path.join(target_dir, "ic_launcher_round.png")
        run_magick([
            source_path,
            "-gravity", "center",
            "-extent", "%[fx:w<h?w:h]x%[fx:w<h?w:h]",
            "-resize", f"{size}x{size}",
            "(", "+clone", "-threshold", "-1", "-draw", f"circle {size/2},{size/2} {size/2},0", ")",
            "-alpha", "off", "-compose", "copy_opacity", "-composite",
            round_path
        ])
        
        print(f"✓ Generated {size}px icons in {folder}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python runtime/generate_icons.py <path_to_source_image>")
    else:
        generate_icons(sys.argv[1])
