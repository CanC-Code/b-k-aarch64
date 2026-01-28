import os
import yaml
import struct
import argparse

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
                # Splat format: [offset, type, name, ...]
                if isinstance(sub, list) and len(sub) >= 3:
                    asset_entries.append({
                        'offset': sub[0],
                        'type': str(sub[1])[:7],
                        'name': str(sub[2])[:31]
                    })
    
    # Sort by offset to ensure size calculation via delta is accurate
    asset_entries.sort(key=lambda x: x['offset'])
    return asset_entries

def write_binary_manifest(entries, output_path):
    if not entries:
        print(f"No entries to write for {output_path}")
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'wb') as f:
        # Header: Entry Count (4 bytes, Little Endian)
        f.write(struct.pack('<I', len(entries)))
        
        for i in range(len(entries)):
            entry = entries[i]
            offset = entry['offset']
            
            # Calculate size accurately
            if i < len(entries) - 1:
                size = entries[i+1]['offset'] - offset
            else:
                # For the last entry, we default to 0 or a large buffer 
                # (The C++ side handles 0 by attempting a safe read)
                size = 0 
                
            name_bin = entry['name'].encode('ascii', 'ignore').ljust(32, b'\0')
            type_bin = entry['type'].encode('ascii', 'ignore').ljust(8, b'\0')
            
            # Entry: Offset(I), Size(I), Name(32s), Type(8s) = 48 bytes
            f.write(struct.pack('<II32s8s', offset, size, name_bin, type_bin))
            
    print(f"Created manifest: {output_path} ({len(entries)} entries, {len(entries)*48 + 4} bytes)")

def main():
    # Assume script is in a 'tools' or 'scripts' folder relative to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir) 

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
