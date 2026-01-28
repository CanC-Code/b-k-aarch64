#include <map>
#include <string>
#include <vector>
#include <cstdio>
#include <android/log.h>
#include <cstdlib>
#include "../rare_decompression.h" // Uses your existing decompressor

#define LOG_TAG "ResourceMgr"

struct AssetEntry {
    uint32_t offset;
    char type[8];
    char name[32];
};

static std::map<uint32_t, AssetEntry> g_manifest;
static std::string g_otrPath;

extern "C" {

void ResourceMgr_Init(const char* otrPath, uint8_t* manifestBuf, uint32_t manifestSize) {
    g_otrPath = otrPath;
    g_manifest.clear();

    if (!manifestBuf) return;

    // Header: Entry Count (4 bytes)
    uint32_t entryCount = *(uint32_t*)manifestBuf;
    AssetEntry* entries = (AssetEntry*)(manifestBuf + 4);

    for (uint32_t i = 0; i < entryCount; i++) {
        g_manifest[entries[i].offset] = entries[i];
    }

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Loaded %d asset entries from manifest", entryCount);
}

void ResourceMgr_HandleDma(void* dramAddr, uint32_t devAddr, uint32_t size) {
    FILE* f = fopen(g_otrPath.c_str(), "rb");
    if (!f) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Could not open OTR file!");
        return;
    }

    // Seek to the ROM address (The OTR is a 1:1 binary dump of assets)
    fseek(f, devAddr, SEEK_SET);

    // Read a small header to check for Rare compression (0x1172)
    uint16_t magic = 0;
    fread(&magic, 2, 1, f);
    fseek(f, devAddr, SEEK_SET); // Reset

    if (magic == 0x1172) { // RZIP / Rare Compression
        uint8_t* compressedBuf = (uint8_t*)malloc(size);
        fread(compressedBuf, 1, size, f);
        
        // Use the decompression function from your rare_decompression.cpp
        // Note: You may need to adjust arguments based on your specific implementation
        rare_decompress(compressedBuf, (uint8_t*)dramAddr, size);
        
        free(compressedBuf);
    } else {
        // Raw Data DMA
        fread(dramAddr, 1, size, f);
    }

    fclose(f);
}

}
