#ifndef ASSETS_MANIFEST_H
#define ASSETS_MANIFEST_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

// Ensure the binary layout is exact to avoid crashes when reading from disk
#pragma pack(push, 1)

enum AssetType {
    ASSET_TYPE_SKIP = 0,
    ASSET_TYPE_COMPRESSED = 1,
    ASSET_TYPE_RAW = 2
};

struct AssetEntry {
    uint32_t romOffset;     // Offset in the ROM file
    uint32_t compSize;      // Size of data in ROM
    uint32_t decompSize;    // Expected size after decompression
    uint32_t type;          // Maps to AssetType
    char name[128];         // Increased to 128 to match common path lengths
};

struct ManifestHeader {
    uint32_t magic;         // 'BKAM' (0x424B414D)
    uint32_t entryCount;    // Total number of AssetEntry structs following header
    uint32_t version;       // Versioning for future-proofing
};

#pragma pack(pop)

#ifdef __cplusplus
}
#endif

#endif // ASSETS_MANIFEST_H
