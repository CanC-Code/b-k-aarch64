#include "otr_builder.h"
#include "assets_manifest.h"
#include <android/log.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <vector>
#include <string>

#define TAG "BKA_OTR"

// Detects region from ROM Header offset 0x3E
int detect_rom_version(const uint8_t* rom_data, size_t size) {
    if (size < 0x40) return ROM_VERSION_UNKNOWN;
    
    char region = (char)rom_data[0x3E];
    __android_log_print(ANDROID_LOG_INFO, TAG, "Detected ROM Region Code: %c", region);

    if (region == 'E') return ROM_VERSION_US;
    if (region == 'P') return ROM_VERSION_PAL;
    
    return ROM_VERSION_UNKNOWN;
}

void extract_assets_to_otr(AAssetManager* mgr, uint8_t* rom_data, size_t rom_size) {
    int version = detect_rom_version(rom_data, rom_size);
    const char* manifest_path = (version == ROM_VERSION_PAL) ? "manifest_pal.bin" : "manifest_us.bin";

    AAsset* asset = AAssetManager_open(mgr, manifest_path, AASSET_MODE_BUFFER);
    if (!asset) {
        __android_log_print(ANDROID_LOG_ERROR, TAG, "Could not open manifest: %s", manifest_path);
        return;
    }

    uint32_t entryCount = 0;
    AAsset_read(asset, &entryCount, sizeof(uint32_t));
    
    // Pointer to the start of entries in the asset buffer
    const AssetEntry* entries = (const AssetEntry*)((const uint8_t*)AAsset_getBuffer(asset) + sizeof(uint32_t));

    __android_log_print(ANDROID_LOG_INFO, TAG, "Starting extraction of %u assets", entryCount);

    for (uint32_t i = 0; i < entryCount; i++) {
        // Logic for decompress_rare_asset will go here in the next step
        // For now, we just validate the manifest reading
        if (i % 500 == 0) {
            __android_log_print(ANDROID_LOG_DEBUG, TAG, "Verified Asset %u: %s at 0x%08X", i, entries[i].name, entries[i].offset);
        }
    }

    AAsset_close(asset);
}
