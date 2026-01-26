import yaml
import os

def generate():
    # Check project root for assets.yaml
    yaml_path = "assets.yaml" 
    output_path = "Android/app/src/main/cpp/assets_manifest.h"

    if not os.path.exists(yaml_path):
        print(f"Error: {yaml_path} not found. Please ensure assets.yaml is in the project root.")
        return

    print(f"Reading {yaml_path}...")
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    files = data.get('files', [])

    with open(output_path, 'w') as f:
        f.write("// Auto-generated asset manifest\n")
        f.write("#ifndef ASSETS_MANIFEST_H\n#define ASSETS_MANIFEST_H\n\n")
        f.write("#include <stdint.h>\n\n")
        
        f.write("struct AssetEntry {\n")
        f.write("    uint32_t uid;\n")
        f.write("    uint32_t size;\n")
        f.write("    const char* name;\n")
        f.write("    const char* type;\n")
        f.write("};\n\n")
        
        f.write(f"static const int g_assets_count = {len(files)};\n\n")
        f.write("static const AssetEntry g_assets_manifest[] = {\n")
        
        for entry in files:
            uid = entry.get('uid', 0)
            size = entry.get('size', 0)
            name = entry.get('name', 'unknown')
            atype = entry.get('type', 'DATA')
            f.write(f'    {{ {uid}, {size}, "{name}", "{atype}" }},\n')
            
        f.write("};\n\n")
        f.write("#endif\n")

    print(f"Generated {output_path} with {len(files)} assets.")

if __name__ == "__main__":
    generate()
