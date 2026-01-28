#include <map>
#include <string>
#include <vector>
#include <cstdio>
#include <android/log.h>

#define LOG_TAG "ResourceMgr"

struct AssetEntry {
    uint32_t offset;
    char type[8];
    char name[32];
};

// Map of ROM Offset -> Asset metadata
static std::map<uint32_t, AssetEntry> g_manifest;
static std::string g_otrPath;

extern "C" {

void ResourceMgr_Init(const char* otrPath, uint8_t* manifestBuf, uint32_t manifestSize) {
    g_otrPath = otrPath;
    
    // The manifestBuf comes from the asset manager in NativeBridge
    uint32_t entryCount = *(uint32_t*)manifestBuf;
    AssetEntry* entries = (AssetEntry*)(manifestBuf + 4);

    for (uint32_t i = 0; i < entryCount; i++) {
        g_manifest[entries[i].offset] = entries[i];
    }

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Loaded %d asset entries from manifest", entryCount);
}

// This is what the N64 DMA/Load functions will call
void* ResourceMgr_LoadFromROM(uint32_t romOffset, uint32_t size) {
    if (g_manifest.find(romOffset) == g_manifest.end()) {
        __android_log_print(ANDROID_LOG_WARN, LOG_TAG, "Warning: Accessing unmanifested ROM offset 0x%08X", romOffset);
        // Fallback: Read raw from the OTR at this offset
    }
    
    // In a "proper" implementation, this returns a pointer to the 
    // decompressed data for the engine to use.
    return nullptr; 
}

}
