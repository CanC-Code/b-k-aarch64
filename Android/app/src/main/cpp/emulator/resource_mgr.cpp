#include <sched.h> // Keep at the very top
#include <map>
#include <string>
#include <vector>
#include <cstdio>
#include <android/log.h>
#include <cstdlib>
#include <cstring>

// Ensure sched_yield is visible in global scope for modern NDK
#ifdef __cplusplus
extern "C" {
#endif
    #include <sched.h>
#ifdef __cplusplus
}
#endif

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

/**
 * Initializes the Resource Manager with the path to the OTR file 
 * and the manifest buffer loaded from Android assets.
 */
void ResourceMgr_Init(const char* otrPath, uint8_t* manifestBuf, uint32_t manifestSize) {
    if (!otrPath) return;
    
    g_otrPath = otrPath;
    g_manifest.clear();

    if (!manifestBuf || manifestSize < 4) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Invalid manifest buffer provided.");
        return;
    }

    // Header: Entry Count (4 bytes)
    uint32_t entryCount = 0;
    memcpy(&entryCount, manifestBuf, 4);

    // Calculate how many entries we can actually read based on buffer size
    uint32_t maxPossibleEntries = (manifestSize - 4) / sizeof(AssetEntry);
    if (entryCount > maxPossibleEntries) {
        entryCount = maxPossibleEntries;
    }

    AssetEntry* entries = (AssetEntry*)(manifestBuf + 4);

    for (uint32_t i = 0; i < entryCount; i++) {
        g_manifest[entries[i].offset] = entries[i];
    }

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Loaded %u asset entries from manifest", entryCount);
}

/**
 * Handles N64-style DMA requests. 
 * Detects Rare (0x1172) compression and decompresses on the fly.
 */
void ResourceMgr_HandleDma(void* dramAddr, uint32_t devAddr, uint32_t size) {
    if (g_otrPath.empty()) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "DMA attempted before ResourceMgr_Init!");
        return;
    }

    FILE* f = fopen(g_otrPath.c_str(), "rb");
    if (!f) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Could not open OTR file: %s", g_otrPath.c_str());
        return;
    }

    // Seek to the ROM address provided by the game engine
    if (fseek(f, devAddr, SEEK_SET) != 0) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Fseek failed at 0x%08X", devAddr);
        fclose(f);
        return;
    }

    // Check for Rare compression (0x1172) magic header
    uint8_t magicHeader[2];
    bool isCompressed = false;
    if (fread(magicHeader, 1, 2, f) == 2) {
        uint16_t magic = (magicHeader[0] << 8) | magicHeader[1];
        if (magic == 0x1172) {
            isCompressed = true;
        }
    }
    
    // Reset file pointer to the start of the DMA block
    fseek(f, devAddr, SEEK_SET);

    if (isCompressed) {
        uint8_t* compressedBuf = (uint8_t*)malloc(size);
        if (compressedBuf) {
            size_t readBytes = fread(compressedBuf, 1, size, f);
            uint32_t outSize = 0;

            // Decompress using the Rare algorithm
            uint8_t* decompressedData = decompress_rare_asset(compressedBuf, (uint32_t)readBytes, &outSize);

            if (decompressedData) {
                // Copy to simulated N64 DRAM
                memcpy(dramAddr, decompressedData, outSize);
                free(decompressedData);
            } else {
                __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Rare decompression failed at 0x%08X", devAddr);
            }
            free(compressedBuf);
        }
    } else {
        // Standard uncompressed DMA
        fread(dramAddr, 1, size, f);
    }

    fclose(f);
    
    // Explicitly call yield to prevent CPU hogging during heavy asset loading
    sched_yield();
}

} // extern "C"
