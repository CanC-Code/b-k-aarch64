#ifndef ASSETS_MANIFEST_H
#define ASSETS_MANIFEST_H

#include <stdint.h>

// Ensure no padding is added by the compiler so it matches our Python struct.pack
#pragma pack(push, 1)

struct AssetEntry {
    uint32_t offset;    // Offset in the original ROM
    char name[32];      // Internal file name
    char type[8];       // Type (bin, c, vtx, etc)
};

struct ManifestHeader {
    uint32_t entryCount;
};

#pragma pack(pop)

#define ROM_VERSION_UNKNOWN 0
#define ROM_VERSION_US      1
#define ROM_VERSION_PAL     2

#endif // ASSETS_MANIFEST_H
