#ifndef ASSETS_MANIFEST_H
#define ASSETS_MANIFEST_H

#include <stdint.h>

#define ASSET_TYPE_SKIP 0
#define ASSET_TYPE_RAW  1

typedef struct {
    uint32_t romOffset;
    uint32_t compSize;
    uint32_t type;
    char name[128];
} AssetEntry;

typedef struct {
    uint32_t magic;      // e.g., 0x424B4101
    uint32_t entryCount;
} ManifestHeader;

#endif
