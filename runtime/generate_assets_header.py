import os

def generate():
    output_path = "Android/app/src/main/cpp/ultra/assets_manifest.h"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        f.write("#ifndef ASSETS_MANIFEST_H\n")
        f.write("#define ASSETS_MANIFEST_H\n\n")
        f.write("#include <stdint.h>\n\n")
        
        f.write("// Structure to hold asset metadata loaded at runtime\n")
        f.write("struct AssetEntry {\n")
        f.write("    uint32_t uid;\n")
        f.write("    uint32_t size;\n")
        f.write("    char name[64];\n")
        f.write("    char type[32];\n")
        f.write("};\n\n")

        f.write("// ROM Version Identifiers\n")
        f.write("#define ROM_VERSION_UNKNOWN 0\n")
        f.write("#define ROM_VERSION_US      1\n")
        f.write("#define ROM_VERSION_PAL     2\n\n")
        
        f.write("#endif\n")

    print(f"Generated structural header at {output_path}")

if __name__ == "__main__":
    generate()
