#pragma once

#include <vector>
#include <cstdint>
#include <string>
#include <android/asset_manager.h>

// Single segment entry
struct OTRSegmentEntry {
    uint32_t rom_offset;
    uint32_t segment_type;
};

// ROM info for version detection
struct RomInfo {
    std::string version;   // e.g., "USv1.0", "PAL"
    std::string region;    // Optional
};

// Main generator class
class OTRGenerator {
public:
    // Generate OTR in memory from ROM bytes + YAML content
    bool generateOTR(const uint8_t* romData, size_t romSize,
                     const char* yamlData, size_t yamlSize,
                     std::vector<uint8_t>& outOTR);

    // Load YAML from Android assets
    static std::vector<uint8_t> loadYAMLAsset(AAssetManager* mgr, const char* filename);

    // Simple ROM version detection stub
    static bool detectRomVersion(const uint8_t* romData, size_t romSize, RomInfo& outInfo);

private:
    bool parseYAML(const char* yamlData, size_t yamlSize,
                   std::vector<OTRSegmentEntry>& entries);

    uint32_t segmentTypeId(const std::string& typeStr);
};