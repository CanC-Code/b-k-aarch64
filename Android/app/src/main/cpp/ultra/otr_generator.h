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
    // Generates OTR binary in-memory from ROM and YAML data
    // Returns true on success, false on failure
    static bool generateOTR(
        const uint8_t* romData,
        size_t romSize,
        const char* yamlData,
        size_t yamlSize,
        std::vector<uint8_t>& outOTR
    );

private:
    // Minimal YAML parser: fills entries vector
    static bool parseYAML(const char* yamlData, size_t yamlSize,
                          std::vector<OTRSegmentEntry>& entries);

    // Converts segment type string to ID
    static uint32_t segmentTypeId(const std::string& typeStr);
};