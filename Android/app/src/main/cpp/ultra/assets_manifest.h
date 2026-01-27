// Android/app/src/main/cpp/ultra/assets_manifest.h
#ifndef ASSETS_MANIFEST_H
#define ASSETS_MANIFEST_H

#include <stdint.h>

#pragma pack(push, 1)

// Maps to the 'file_type_to_asset_type' logic in generate_asset_enums.py
enum AssetType : uint8_t {
    ASSET_TYPE_ANIM   = 0,
    ASSET_TYPE_MODEL  = 1,
    ASSET_TYPE_SPRITE = 2,
    ASSET_TYPE_DIALOG = 3,
    ASSET_TYPE_SKIP   = 255 
};

struct AssetEntry {
    uint32_t uid;           // Asset ID (e.g. 0x1516)
    uint32_t romOffset;     [span_1](start_span)// Calculated offset in the ROM[span_1](end_span)
    uint32_t compSize;      // Size to read from ROM
    uint32_t decompSize;    // Expected output size
    uint8_t  type;          // AssetType enum
    char name[32];          [span_2](start_span)// Human-readable name[span_2](end_span)
};

struct ManifestHeader {
    uint32_t magic;         // 'BKAR'
    uint32_t entryCount;    [span_3](start_span)//[span_3](end_span)
};

#pragma pack(pop)
#endif
