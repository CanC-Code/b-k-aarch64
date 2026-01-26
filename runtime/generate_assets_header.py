import yaml
import os
import sys

def generate():
    # 1. Determine the correct path for assets.yaml
    # We check root, and then the Android-specific asset folder found in your logs
    possible_yaml_paths = [
        "assets.yaml",
        "Android/app/src/main/cpp/assets/assets.yaml"
    ]
    
    yaml_path = None
    for path in possible_yaml_paths:
        if os.path.exists(path):
            yaml_path = path
            break
            
    if not yaml_path:
        print(f"Error: assets.yaml not found in {possible_yaml_paths}")
        print("Please ensure assets.yaml exists.")
        sys.exit(1)

    # 2. Define output path
    output_path = "Android/app/src/main/cpp/ultra/assets_manifest.h"
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Reading from: {yaml_path}")
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    files = data.get('files', [])

    with open(output_path, 'w') as f:
        f.write("#ifndef ASSETS_MANIFEST_H\n")
        f.write("#define ASSETS_MANIFEST_H\n\n")
        f.write("#include <stdint.h>\n\n")
        f.write("struct AssetEntry { uint32_t uid; uint32_t size; const char* name; const char* type; };\n\n")
        f.write(f"static const int g_assets_count = {len(files)};\n")
        f.write("static const AssetEntry g_assets_manifest[] = {\n")
        for entry in files:
            f.write(f'    {{ {entry.get("uid",0)}, {entry.get("size",0)}, "{entry.get("name","")}", "{entry.get("type","")}" }},\n')
        f.write("};\n\n")
        f.write("#endif\n")

    print(f"Successfully generated manifest at: {output_path}")

if __name__ == "__main__":
    generate()
