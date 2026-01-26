#include <jni.h>
#include <vector>
#include <string>
#include <fcntl.h>
#include <unistd.h>
#include "assets.h" // This header is generated from assets.yaml at build time

extern "C" {

void core1_loadOTR(int fd) {
    // 1. Read the ROM into memory (or use mmap for efficiency)
    off_t size = lseek(fd, 0, SEEK_END);
    lseek(fd, 0, SEEK_SET);
    std::vector<uint8_t> rom_data(size);
    read(fd, rom_data.data(), size);

    // 2. Iterate through assets (mirroring generate_asset_enums.py logic)
    for (const auto& asset : g_assets_manifest) {
        // g_assets_manifest is an array of {uid, size, type} from the YAML
        uint32_t offset = asset.uid;
        uint32_t len = asset.size;

        if (offset + len > rom_data.size()) continue;

        std::vector<uint8_t> raw_asset(rom_data.begin() + offset, rom_data.begin() + offset + len);
        std::vector<uint8_t> decompressed;

        // 3. Decompress if header exists
        if (decompress_rare_asset(raw_asset, decompressed)) {
            // Process the modern asset (e.g., convert to PNG if it's a sprite)
            save_to_otr(asset.name, decompressed);
        } else {
            save_to_otr(asset.name, raw_asset);
        }
    }
}

}
