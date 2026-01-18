#pragma once
#include <vector>
#include <cstdint>
#include <string>
#include <android/asset_manager_jni.h>
#include "otr_generator.h"

// Build OTR using embedded YAML per ROM version
inline bool buildOTRForROM(AAssetManager* mgr,
                            const uint8_t* romData,
                            size_t romSize,
                            std::vector<uint8_t>& outOTR)
{
    OTRGenerator::RomInfo info{};
    if (!OTRGenerator::detectRomVersion(romData, romSize, info)) return false;

    std::string yamlFile;
    if (info.version == "USv1.0") yamlFile = "otr_yaml/decompressed.us.v10.yaml";
    else if (info.version == "PAL") yamlFile = "otr_yaml/decompressed.pal.yaml";
    else return false; // unsupported version

    std::vector<uint8_t> yamlBuf = OTRGenerator::loadYAMLAsset(mgr, yamlFile.c_str());
    if (yamlBuf.empty()) return false;

    OTRGenerator gen;
    return gen.generateOTR(
        romData,
        romSize,
        reinterpret_cast<const char*>(yamlBuf.data()),
        yamlBuf.size(),
        outOTR
    );
}

// Legacy: SHA1 → BIN loader (if needed)
bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    const char* yamlData,
    size_t yamlSize,
    std::vector<uint8_t>& outOTR
);