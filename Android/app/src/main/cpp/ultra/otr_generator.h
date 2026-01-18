#pragma once
#include <vector>
#include <cstdint>
#include <string>

struct OTRSegmentEntry {
    uint32_t romOffset;
    uint32_t segmentType;
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

    static bool detectRomVersion(
        const uint8_t* romData,
        size_t romSize,
        struct OTRBuilder::RomInfo& outInfo
    );

    static std::string sha1Hex(const uint8_t* data, size_t len);
};