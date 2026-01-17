#!/usr/bin/env python3
"""
yaml_to_otr_bin.py

Compile a Banjo-Kazooie decompressed YAML layout into a compact
binary OTR asset index usable at runtime.

Author: CCVO
"""

import sys
import yaml
import struct
from pathlib import Path

MAGIC = b"BKOTR\0\0\0"  # 8 bytes
VERSION = 1

# Segment type IDs (stable ABI)
SEGMENT_TYPE_IDS = {
    "bin": 1,
    "code": 2,
    "header": 3,
}

def die(msg):
    print(f"[yaml2bin] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)

def main():
    if len(sys.argv) != 3:
        die("Usage: yaml_to_otr_bin.py <input.yaml> <output.bin>")

    yaml_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    if not yaml_path.exists():
        die(f"Input YAML not found: {yaml_path}")

    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        die("Top-level YAML must be a mapping")

    segments = data.get("segments")
    if not isinstance(segments, list):
        die("YAML missing 'segments' list")

    entries = []

    for seg in segments:
        if not isinstance(seg, dict):
            continue

        seg_type = seg.get("type")
        seg_start = seg.get("start")
        subsegments = seg.get("subsegments")

        if seg_type not in SEGMENT_TYPE_IDS:
            continue

        if not isinstance(seg_start, int):
            continue

        if not isinstance(subsegments, list):
            continue

        for sub in subsegments:
            # Expected form:
            # [rom_offset, kind, name]
            if not isinstance(sub, list) or len(sub) < 2:
                continue

            rom_offset = sub[0]
            kind = sub[1]

            if kind != "bin":
                continue

            if not isinstance(rom_offset, int):
                continue

            entries.append({
                "rom_offset": rom_offset,
                "segment_type": SEGMENT_TYPE_IDS[seg_type],
            })

    if not entries:
        die("No bin subsegments found")

    # Sort deterministically by ROM offset
    entries.sort(key=lambda e: e["rom_offset"])

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("wb") as f:
        # Header
        f.write(MAGIC)
        f.write(struct.pack("<I", VERSION))
        f.write(struct.pack("<I", len(entries)))

        # Entries
        for e in entries:
            f.write(struct.pack(
                "<II",
                e["rom_offset"],
                e["segment_type"]
            ))

    print(f"[yaml2bin] OK: wrote {len(entries)} entries to {out_path}")

if __name__ == "__main__":
    main()