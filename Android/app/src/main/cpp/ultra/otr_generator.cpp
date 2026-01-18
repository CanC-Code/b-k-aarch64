#include "otr_generator.hpp"
#include <cstring>
#include <stdexcept>

bool OTRGenerator::detectRomVersion(const uint8_t* romData, size_t romSize, RomInfo& outInfo) {
    // Simple detection placeholder
    if (romSize >= 4) {
        if (romData[0] == 'U') outInfo.version = "USv1.0";
        else if (romData[0] == 'P') outInfo.version = "PAL";
        else return false;
        return true;
    }
    return false;
}

std::vector<uint8_t> OTRGenerator::loadYAMLAsset(void* mgr, const char* assetPath) {
    // Android asset manager loading placeholder
    std::vector<uint8_t> buf;

    // In real implementation, cast to AAssetManager* and read the file
    // For now return empty if assetPath is missing
    return buf;
}

bool OTRGenerator::generateOTR(const uint8_t* romData,
                               size_t romSize,
                               const char* yamlData,
                               size_t yamlSize,
                               std::vector<uint8_t>& outOTR) {
    if (!romData || !yamlData) return false;

    size_t totalSteps = 100; // fake progress steps
    outOTR.clear();
    outOTR.reserve(romSize + yamlSize);

    for (size_t i = 0; i < totalSteps; ++i) {
        // Simulate work
        float progress = static_cast<float>(i) / static_cast<float>(totalSteps);
        reportProgress(progress);
    }

    // Simple mock: combine ROM + YAML
    outOTR.insert(outOTR.end(), romData, romData + romSize);
    outOTR.insert(outOTR.end(), yamlData, yamlData + yamlSize);

    reportProgress(1.0f);
    return true;
}