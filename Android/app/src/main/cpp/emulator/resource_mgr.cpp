#include <sched.h>
#include <map>
#include <string>
#include <vector>
#include <cstdio>
#include <android/log.h>
#include <cstdlib>
#include <cstring>
#include "../tools/rare_decompression.h" 

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
    // Using memcpy to avoid potential alignment issues on ARM64
    uint32_t entryCount;
    memcpy(&entryCount, manifestBuf, 4);
    
    AssetEntry* entries = (AssetEntry*)(manifestBuf + 4);

    for (uint32_t i = 0; i < entryCount; i++) {
        g_manifest[entries[i].offset] = entries[i];
    }

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Loaded %u asset entries from manifest", entryCount);
}

void ResourceMgr_HandleDma(void* dramAddr, uint32_t devAddr, uint32_t size) {
    FILE* f = fopen(g_otrPath.c_str(), "rb");
    if (!f) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Could not open OTR file!");
        return;
    }

    // Seek to the ROM address
    fseek(f, devAddr, SEEK_SET);

    // Read magic to check for Rare compression (0x1172)
    uint8_t magicHeader[2];
    if (fread(magicHeader, 1, 2, f) != 2) {
        fclose(f);
        return;
    }
    uint16_t magic = (magicHeader[0] << 8) | magicHeader[1];
    fseek(f, devAddr, SEEK_SET); // Reset pointer for full read

    if (magic == 0x1172) { // RZIP / Rare Compression
        uint8_t* compressedBuf = (uint8_t*)malloc(size);
        if (compressedBuf) {
            fread(compressedBuf, 1, size, f);

            uint32_t outSize = 0;
            // FIXED: Using the correct function from rare_decompression.h
            uint8_t* decompressedData = decompress_rare_asset(compressedBuf, size, &outSize);

            if (decompressedData) {
                // Copy the decompressed data to the target DRAM address
                // We use outSize to ensure we don't copy more than was produced
                memcpy(dramAddr, decompressedData, outSize);
                free(decompressedData);
            } else {
                __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Rare decompression failed at 0x%08X", devAddr);
            }
            free(compressedBuf);
        }
    } else {
        // Raw Data DMA
        fread(dramAddr, 1, size, f);
    }

    fclose(f);
}

}
