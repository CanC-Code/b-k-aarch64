#ifndef ASSETS_MANIFEST_H
#define ASSETS_MANIFEST_H

#include <cstdint>

enum AssetType {
    ASSET_TYPE_SKIP = 0,
    ASSET_TYPE_COMPRESSED = 1,
    ASSET_TYPE_RAW = 2
};

#pragma pack(push, 1)
struct AssetEntry {
    uint32_t romOffset;     // Calculated offset in the ROM
    uint32_t compSize;      // Size of data in ROM (compressed)
    uint32_t decompSize;    // Expected output size
    uint32_t type;          // AssetType
    char name[32];          // Human-readable name
};

struct ManifestHeader {
    uint32_t magic;         // e.g., 0x424B414D 'BKAM'
    uint32_t entryCount;    // Total number of assets
    uint32_t version;       // Version of the manifest format
};
#pragma pack(pop)

#endif
