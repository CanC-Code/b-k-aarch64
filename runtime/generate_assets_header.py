import os

def generate():
    # Use absolute path discovery to ensure it lands in the right place regardless of CWD
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_dir, "Android/app/src/main/cpp/ultra/assets_manifest.h")
    
    print(f"Generating manifest at: {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        f.write("#ifndef ASSETS_MANIFEST_H\n#define ASSETS_MANIFEST_H\n\n")
        f.write("#include <stdint.h>\n\n")
        f.write("struct AssetEntry { uint32_t uid; uint32_t size; char name[128]; char type[64]; };\n\n")
        
        # Add basic definitions
        f.write("#define ROM_VERSION_UNKNOWN 0\n")
        f.write("#define ROM_VERSION_US      1\n")
        f.write("#define ROM_VERSION_PAL     2\n\n")
        
        # If you have an assets.yaml, you can parse it here to populate a manifest array
        # For now, we provide an empty or default array to satisfy the compiler
        f.write("static const AssetEntry g_assets_manifest[] = {\n")
        f.write("    { 0, 0, \"terminator\", \"none\" }\n")
        f.write("};\n\n")
        
        f.write("#endif\n")

if __name__ == "__main__":
    generate()
