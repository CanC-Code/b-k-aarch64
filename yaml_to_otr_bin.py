#!/usr/bin/env python3
import sys
import struct
import yaml

MAGIC = 0x424B4F54  # 'BKOT'
VERSION = 1

COMPRESSION_MAP = {
    "raw": 0,
    "rzip": 1,
}

def die(msg):
    print(f"[yaml2bin] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def main(yaml_path, bin_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, list):
        die("Top-level YAML must be a list")

    entries = []
    string_table = bytearray()
    string_offsets = {}

    def intern_string(s: str) -> int:
        if s in string_offsets:
            return string_offsets[s]
        offset = len(string_table)
        string_table.extend(s.encode("utf-8") + b"\x00")
        string_offsets[s] = offset
        return offset

    for i, asset in enumerate(data):
        if not isinstance(asset, dict):
            die(f"Entry {i} is not a mapping")

        try:
            name = asset["name"]
            rom_start = int(asset["rom_start"], 0)
            rom_end = int(asset["rom_end"], 0)
            typ = asset.get("type", "raw")
        except KeyError as e:
            die(f"Missing key {e} in entry {i}")

        if rom_end <= rom_start:
            die(f"Invalid ROM range in entry {i}")

        if typ not in COMPRESSION_MAP:
            die(f"Unknown compression type '{typ}' in entry {i}")

        decompressed_size = int(asset.get("decompressed_size", 0), 0)

        name_off = intern_string(name)

        entries.append((
            name_off,
            rom_start,
            rom_end,
            decompressed_size,
            COMPRESSION_MAP[typ],
        ))

    with open(bin_path, "wb") as out:
        out.write(struct.pack("<III", MAGIC, VERSION, len(entries)))

        for e in entries:
            out.write(struct.pack(
                "<IIIIB3s",
                e[0],
                e[1],
                e[2],
                e[3],
                e[4],
                b"\x00\x00\x00",
            ))

        out.write(string_table)

    print(f"[yaml2bin] Wrote {len(entries)} assets to {bin_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        die("Usage: yaml_to_otr_bin.py input.yaml output.bin")
    main(sys.argv[1], sys.argv[2])