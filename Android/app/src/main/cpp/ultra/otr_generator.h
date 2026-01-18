#pragma once
#include <vector>
#include <cstdint>
#include <string>

struct OTRSegmentEntry {
    uint32_t rom_offset;
    uint32_t segment_type;
};

class OTRGenerator {
public:
    OTRGenerator() = default;

    // Generate OTR in memory from ROM + YAML
    bool generateOTR(
        const uint8_t* romData,
        size_t romSize,
        const char* yamlData,
        size_t yamlSize,
        std::vector<uint8_t>& outOTR
    );

    // Minimal YAML parser for our subset (segments/subsegments)
    bool parseYAML(
        const char* yamlData,
        size_t yamlSize,
        std::vector<OTRSegmentEntry>& entries
    );

    // Helper: segment type string -> ID
    uint32_t segmentTypeId(const std::string& typeStr);

    // ROM version detection
    struct RomInfo {
        std::string version;
        std::string region;
        std::string gameId;
    };

    static bool detectRomVersion(
        const uint8_t* romData,
        size_t romSize,
        RomInfo& outInfo
    );

    // Asset loader from AssetManager
    static std::vector<uint8_t> loadYAMLAsset(void* assetManager, const char* path);
};