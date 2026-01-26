import os

def generate():
    output_path = "Android/app/src/main/cpp/ultra/assets_manifest.h"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        f.write("#ifndef ASSETS_MANIFEST_H\n#define ASSETS_MANIFEST_H\n\n")
        f.write("#include <stdint.h>\n\n")
        f.write("struct AssetEntry { uint32_t uid; uint32_t size; char name[128]; char type[64]; };\n\n")
        f.write("#define ROM_VERSION_UNKNOWN 0\n")
        f.write("#define ROM_VERSION_US      1\n")
        f.write("#define ROM_VERSION_PAL     2\n\n")
        f.write("#endif\n")

if __name__ == "__main__":
    generate()
