#ifndef OTR_BUILDER_H
#define OTR_BUILDER_H

#include <vector>
#include <cstdint>

#ifdef __cplusplus
extern "C" {
#endif

// Detects 0 for US, 1 for PAL
int detect_rom_version(const uint8_t* romData, size_t size);

// Handles Rare-specific asset decompression
void decompress_rare_asset(const std::vector<uint8_t>& input, std::vector<uint8_t>& output);

// Main entry point for OTR generation
void extract_assets_to_otr(const uint8_t* romData, size_t size, const char* outPath);

#ifdef __cplusplus
}
#endif

#endif // OTR_BUILDER_H
