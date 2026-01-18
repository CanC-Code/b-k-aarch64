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

    bool generateOTR(
        const uint8_t* romData,
        size_t romSize,
        const char* yamlData,
        size_t yamlSize,
        std::vector<uint8_t>& outOTR
    );

    bool parseYAML(
        const char* yamlData,
        size_t yamlSize,
        std::vector<OTRSegmentEntry>& entries
    );

    uint32_t segmentTypeId(const std::string& typeStr);

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

    static std::vector<uint8_t> loadYAMLAsset(void* assetManager, const char* path);
};