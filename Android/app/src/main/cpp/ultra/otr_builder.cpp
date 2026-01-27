#include "otr_builder.h"
#include "assets_manifest.h"
#include "rare_decompression.h" // You need to ensure this header exists in tools/
#include <android/log.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <vector>
#include <string>
#include <sys/stat.h>
#include <fstream>

#define TAG "BKA_OTR"

extern "C" {

// Helper to ensure directory exists
void make_dir(const std::string& path) {
    mkdir(path.c_str(), 0770);
}

void extract_assets_to_otr(AAssetManager* mgr, uint8_t* rom_data, size_t rom_size, const char* output_path) {
    int version = detect_rom_version(rom_data, rom_size);
    const char* manifest_path = (version == ROM_VERSION_PAL) ? "manifest_pal.bin" : "manifest_us.bin";

    AAsset* asset = AAssetManager_open(mgr, manifest_path, AASSET_MODE_BUFFER);
    if (!asset) return;

    uint32_t entryCount = 0;
    AAsset_read(asset, &entryCount, sizeof(uint32_t));
    const AssetEntry* entries = (const AssetEntry*)((const uint8_t*)AAsset_getBuffer(asset) + sizeof(uint32_t));

    std::string base_path = std::string(output_path) + "/extract/";
    make_dir(base_path);

    for (uint32_t i = 0; i < entryCount; i++) {
        uint32_t offset = entries[i].offset;
        
        // Only attempt decompression if it has the Rare 0x1172 header
        if (rom_data[offset] == 0x11 && rom_data[offset+1] == 0x72) {
            uint32_t out_size = 0;
            // This calls your rare_decompression.cpp logic
            uint8_t* decompressed = decompress_rare_asset(&rom_data[offset], &out_size);
            
            if (decompressed) {
                std::string file_out = base_path + entries[i].name;
                // Create subfolders if needed (e.g., bin/assets/...)
                // Logic to split path and mkdir -p would go here
                
                std::ofstream out(file_out, std::ios::binary);
                out.write((char*)decompressed, out_size);
                out.close();
                
                free(decompressed);
            }
        }
    }
    AAsset_close(asset);
}

} // extern "C"
