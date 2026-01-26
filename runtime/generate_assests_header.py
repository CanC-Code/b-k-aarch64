import yaml
import os

def generate():
    yaml_path = "assets.yaml" # Adjust path if assets.yaml is elsewhere
    output_path = "Android/app/src/main/cpp/assets_manifest.h"

    if not os.path.exists(yaml_path):
        print(f"Error: {yaml_path} not found.")
        return

    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    with open(output_path, 'w') as f:
        f.write("// Auto-generated asset manifest from assets.yaml\n")
        f.write("#ifndef ASSETS_MANIFEST_H\n#define ASSETS_MANIFEST_H\n\n")
        f.write("#include <stdint.h>\n\n")
        f.write("struct AssetEntry {\n")
        f.write("    uint32_t uid;\n")
        f.write("    uint32_t size;\n")
        f.write("    const char* name;\n")
        f.write("    const char* type;\n")
        f.write("};\n\n")
        
        f.write("static const AssetEntry g_assets_manifest[] = {\n")
        
        for file_entry in data.get('files', []):
            uid = file_entry.get('uid', 0)
            size = file_entry.get('size', 0)
            name = file_entry.get('name', 'unknown')
            atype = file_entry.get('type', 'DATA')
            
            # Format as C++ struct entry
            f.write(f'    {{ {uid}, {size}, "{name}", "{atype}" }},\n')
            
        f.write("};\n\n")
        f.write(f"static const int g_assets_count = {len(data.get('files', []))};\n\n")
        f.write("#endif // ASSETS_MANIFEST_H\n")

    print(f"Successfully generated {output_path}")

if __name__ == "__main__":
    generate()
