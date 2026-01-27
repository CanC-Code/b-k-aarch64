#ifndef OTR_BUILDER_H
#define OTR_BUILDER_H

#include <stdint.h>
#include <stddef.h>
#include <android/asset_manager.h>

#ifdef __cplusplus
extern "C" {
#endif

// Defined versions
#define ROM_VERSION_UNKNOWN 0
#define ROM_VERSION_US      1
#define ROM_VERSION_PAL     2

/**
 * Detects the ROM version based on the region code in the header.
 */
int detect_rom_version(const uint8_t* rom_data, size_t size);

/**
 * Main entry point for asset extraction. 
 * Now includes the output_path where files will be saved.
 */
void extract_assets_to_otr(AAssetManager* mgr, uint8_t* rom_data, size_t rom_size, const char* output_path);

#ifdef __cplusplus
}
#endif

#endif // OTR_BUILDER_H
