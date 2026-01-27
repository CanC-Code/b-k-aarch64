// Android/app/src/main/cpp/ultra/assets_manifest.h
#ifndef ASSETS_MANIFEST_H
#define ASSETS_MANIFEST_H

#include <stdint.h>

#pragma pack(push, 1)

// Asset types mirrored from generate_assets_enums.py
enum AssetType : uint8_t {
    ASSET_TYPE_ANIM   = 0,
    ASSET_TYPE_MODEL  = 1,
    ASSET_TYPE_SPRITE = 2,
    ASSET_TYPE_DIALOG = 3,
    ASSET_TYPE_SKIP   = 255
};

struct AssetEntry {
    uint32_t uid;           // Asset ID (e.g. 0x1516)
    uint32_t romOffset;     // Exact byte start in ROM
    uint32_t compSize;      // Size in ROM (to read)
    uint32_t decompSize;    // Expected size (for buffer allocation)
    uint8_t  type;          // AssetType
    char name[32];          // Human-readable name: "ASSET_0001_MODEL.bin"
};

struct ManifestHeader {
    uint32_t magic;         // 0x424B4152 ("BKAR" for Banjo-Kazooie Archive)
    uint32_t version;       // Version of the manifest format
    uint32_t entryCount;    // Number of entries to follow
};

#pragma pack(pop)
#endif
