#include "otr_generator.h"
#include <vector>
#include <string>
#include <cstring>
#include <algorithm>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <sstream>

const char MAGIC[8] = "BKOTR\0\0\0";
const uint32_t VERSION = 1;

// Helper: trim whitespace
static inline std::string trim(const std::string& s) {
    size_t start = s.find_first_not_of(" \t\r\n");
    size_t end = s.find_last_not_of(" \t\r\n");
    return (start == std::string::npos) ? "" : s.substr(start, end - start + 1);
}

// Helper: convert segment type string to ID
uint32_t OTRGenerator::segmentTypeId(const std::string& typeStr) {
    if (typeStr == "bin") return 1;
    if (typeStr == "code") return 2;
    if (typeStr == "header") return 3;
    return 0;
}

// Minimal parser for our subset of YAML
bool OTRGenerator::parseYAML(const char* yamlData, size_t yamlSize,
                             std::vector<OTRSegmentEntry>& entries) {
    std::istringstream stream(std::string(yamlData, yamlSize));
    std::string line;
    std::string currentSegType;
    bool inSegments = false;
    bool inSubsegments = false;

    while (std::getline(stream, line)) {
        line = trim(line);
        if (line.empty() || line[0] == '#') continue;

        if (line.find("segments:") == 0) {
            inSegments = true;
            continue;
        }

        if (inSegments && line.find("- type:") == 0) {
            size_t colon = line.find(":");
            currentSegType = trim(line.substr(colon + 1));
            inSubsegments = false;
            continue;
        }

        if (inSegments && line.find("subsegments:") == 0) {
            inSubsegments = true;
            continue;
        }

        if (inSubsegments && line.find("- [") == 0) {
            // Expected format: - [rom_offset, kind, name]
            size_t start = line.find("[");
            size_t end = line.find("]");
            if (start == std::string::npos || end == std::string::npos) continue;

            std::string inner = line.substr(start + 1, end - start - 1);
            std::istringstream ss(inner);
            std::string item;
            std::vector<std::string> parts;
            while (std::getline(ss, item, ',')) {
                parts.push_back(trim(item));
            }
            if (parts.size() < 2) continue;
            if (parts[1] != "\"bin\"" && parts[1] != "bin") continue;

            uint32_t rom_offset = std::stoul(parts[0]);
            uint32_t seg_id = segmentTypeId(currentSegType);
            if (seg_id == 0) continue;

            entries.push_back({rom_offset, seg_id});
        }
    }

    return !entries.empty();
}

// Main generator
bool OTRGenerator::generateOTR(const uint8_t* romData, size_t romSize,
                               const char* yamlData, size_t yamlSize,
                               std::vector<uint8_t>& outOTR) {
    if (!romData || romSize == 0 || !yamlData || yamlSize == 0) return false;

    std::vector<OTRSegmentEntry> entries;
    if (!parseYAML(yamlData, yamlSize, entries)) return false;

    // Deterministic sort
    std::sort(entries.begin(), entries.end(),
              [](const OTRSegmentEntry& a, const OTRSegmentEntry& b) {
                  return a.rom_offset < b.rom_offset;
              });

    // Calculate output size
    size_t outSize = 8 + sizeof(uint32_t) * 2 + entries.size() * sizeof(OTRSegmentEntry);
    outOTR.resize(outSize);

    uint8_t* ptr = outOTR.data();
    std::memcpy(ptr, MAGIC, 8); ptr += 8;
    std::memcpy(ptr, &VERSION, sizeof(uint32_t)); ptr += sizeof(uint32_t);

    uint32_t entryCount = entries.size();
    std::memcpy(ptr, &entryCount, sizeof(uint32_t)); ptr += sizeof(uint32_t);

    for (const auto& e : entries) {
        std::memcpy(ptr, &e.rom_offset, sizeof(uint32_t)); ptr += sizeof(uint32_t);
        std::memcpy(ptr, &e.segment_type, sizeof(uint32_t)); ptr += sizeof(uint32_t);
    }

    return true;
}