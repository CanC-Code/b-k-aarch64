#ifndef OTR_BUILDER_H
#define OTR_BUILDER_H

#include <stdint.h>
#include <stddef.h>
#include <android/asset_manager.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Detects the ROM version based on the region code in the header.
 * @param rom_data Pointer to the raw ROM bytes
 * @param size Size of the ROM buffer
 * @return ROM_VERSION_US, ROM_VERSION_PAL, or ROM_VERSION_UNKNOWN
 */
int detect_rom_version(const uint8_t* rom_data, size_t size);

/**
 * Main entry point for asset extraction. 
 * Reads the manifest from assets and prepares decompression.
 */
void extract_assets_to_otr(AAssetManager* mgr, uint8_t* rom_data, size_t rom_size);

#ifdef __cplusplus
}
#endif

#endif // OTR_BUILDER_H
