import os
import yaml
import struct

def parse_splat_yaml(yaml_path):
    if not os.path.exists(yaml_path):
        print(f"Skipping {yaml_path}: File not found")
        return []
    
    with open(yaml_path, 'r') as f:
        config = yaml.safe_load(f)
    
    asset_entries = []
    segments = config.get('segments', [])
    
    for seg in segments:
        if isinstance(seg, dict):
            subsegments = seg.get('subsegments', [])
            for sub in subsegments:
                if isinstance(sub, list) and len(sub) >= 3:
                    offset = sub[0]
                    file_type = sub[1]
                    file_name = sub[2]
                    # Format: offset, name (max 32), type (max 8)
                    asset_entries.append({
                        'offset': offset,
                        'name': str(file_name)[:31],
                        'type': str(file_type)[:7]
                    })
    return asset_entries

def write_binary_manifest(entries, output_path):
    if not entries:
        return
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as f:
        # Header: Entry Count (4 bytes)
        f.write(struct.pack('<I', len(entries)))
        for entry in entries:
            # Entry: Offset(I), Name(32s), Type(8s)
            name_bin = entry['name'].encode('ascii', 'ignore').ljust(32, b'\0')
            type_bin = entry['type'].encode('ascii', 'ignore').ljust(8, b'\0')
            f.write(struct.pack('<I32s8s', entry['offset'], name_bin, type_bin))
    print(f"Created binary manifest: {output_path} ({len(entries)} entries)")

def main():
    # Discovery base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Process US Manifest
    us_yaml = os.path.join(base_dir, "decompressed.us.v10.yaml")
    us_out = os.path.join(base_dir, "Android/app/src/main/assets/manifest_us.bin")
    write_binary_manifest(parse_splat_yaml(us_yaml), us_out)
    
    # 2. Process PAL Manifest
    pal_yaml = os.path.join(base_dir, "decompressed.pal.yaml")
    pal_out = os.path.join(base_dir, "Android/app/src/main/assets/manifest_pal.bin")
    write_binary_manifest(parse_splat_yaml(pal_yaml), pal_out)

if __name__ == "__main__":
    main()
