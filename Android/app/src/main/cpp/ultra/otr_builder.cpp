#include "otr_builder.h"
#include "assets_manifest.h"
#include "../tools/rare_decompression.h"
#include <android/log.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <vector>
#include <string>
#include <sys/stat.h>
#include <fstream>
#include <errno.h>

#define TAG "BKA_OTR"

extern "C" {

// Helper to create directories recursively (mkdir -p)
void mkdir_p(const std::string& path) {
    size_t pos = 0;
    std::string current_path;
    while ((pos = path.find('/', pos + 1)) != std::string::npos) {
        current_path = path.substr(0, pos);
        if (mkdir(current_path.c_str(), 0770) && errno != EEXIST) {
            // Handle error if needed
        }
    }
}

void extract_assets_to_otr(AAssetManager* mgr, uint8_t* rom_data, size_t rom_size, const char* output_path) {
    int version = detect_rom_version(rom_data, rom_size);
    const char* manifest_path = (version == ROM_VERSION_PAL) ? "manifest_pal.bin" : "manifest_us.bin";

    AAsset* asset = AAssetManager_open(mgr, manifest_path, AASSET_MODE_BUFFER);
    if (!asset) {
        __android_log_print(ANDROID_LOG_ERROR, TAG, "Failed to open manifest %s", manifest_path);
        return;
    }

    uint32_t entryCount = 0;
    AAsset_read(asset, &entryCount, sizeof(uint32_t));
    const AssetEntry* entries = (const AssetEntry*)((const uint8_t*)AAsset_getBuffer(asset) + sizeof(uint32_t));

    std::string base_extract_dir = std::string(output_path) + "/";

    for (uint32_t i = 0; i < entryCount; i++) {
        uint32_t offset = entries[i].offset;
        
        // Safety check for ROM bounds
        if (offset + 2 >= rom_size) continue;

        // Check for Rare's magic 0x1172 header
        if (rom_data[offset] == 0x11 && rom_data[offset+1] == 0x72) {
            uint32_t out_size = 0;
            uint8_t* decompressed = decompress_rare_asset(&rom_data[offset], &out_size);
            
            if (decompressed) {
                std::string full_file_path = base_extract_dir + entries[i].name;
                
                // Ensure the subdirectory for this file exists
                mkdir_p(full_file_path);

                std::ofstream out(full_file_path, std::ios::binary);
                if (out.is_open()) {
                    out.write((char*)decompressed, out_size);
                    out.close();
                }
                
                free(decompressed);
            }
        } else {
            // If it's not compressed, we might want to copy it raw (optional)
            // For now, we only care about the decompressed research files
        }
    }

    AAsset_close(asset);
    __android_log_print(ANDROID_LOG_INFO, TAG, "Extraction complete!");
}

} // extern "C"
