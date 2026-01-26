# Replace the 'standard_path' block in generate_icons.py with this:
run_magick([
    source_path,
    "-resize", f"{size}x{size}^",
    "-gravity", "center",
    "-extent", f"{size}x{size}",
    "-unsharp", "0x1",
    standard_path
])

# Replace the 'round_path' block with this:
run_magick([
    source_path,
    "-resize", f"{size}x{size}^",
    "-gravity", "center",
    "-extent", f"{size}x{size}",
    "(", "+clone", "-alpha", "extract", "-threshold", "0", 
    "-draw", f"fill black polygon 0,0 0,{size} {size},{size} {size},0 fill white circle {size/2},{size/2} {size/2},0", 
    ")", "-alpha", "off", "-compose", "CopyOpacity", "-composite",
    round_path
])
