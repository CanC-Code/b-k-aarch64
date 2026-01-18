#include "otr_builder.h"
#include "otr_generator.hpp"

#include <vector>
#include <string>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>

bool buildOTRForROM(
    AAssetManager* assetManager,
    const uint8_t* romData,
    size_t romSize,
    std::vector<uint8_t>& outOTR
) {
    if (!romData || romSize == 0 || !assetManager) {
        return false;
    }

    // Detect ROM
    OTRGenerator::RomInfo info{};
    if (!OTRGenerator::detectRomVersion(romData, romSize, info)) {
        return false;
    }

    // Select YAML
    std::string yamlPath;
    if (info.version == "USv1.0") {
        yamlPath = "otr_yaml/decompressed.us.v10.yaml";
    } else if (info.version == "PAL") {
        yamlPath = "otr_yaml/decompressed.pal.yaml";
    } else {
        return false; // unsupported ROM
    }

    // Load YAML from assets
    std::vector<uint8_t> yamlData =
        OTRGenerator::loadYAMLAsset(assetManager, yamlPath.c_str());

    if (yamlData.empty()) {
        return false;
    }

    // Generate OTR
    OTRGenerator generator;
    return generator.generateOTR(
        romData,
        romSize,
        reinterpret_cast<const char*>(yamlData.data()),
        yamlData.size(),
        outOTR
    );
}

// Optional legacy path
bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    const char* yamlData,
    size_t yamlSize,
    std::vector<uint8_t>& outOTR
) {
    if (!romData || !yamlData || romSize == 0 || yamlSize == 0) {
        return false;
    }

    OTRGenerator generator;
    return generator.generateOTR(
        romData,
        romSize,
        yamlData,
        yamlSize,
        outOTR
    );
}