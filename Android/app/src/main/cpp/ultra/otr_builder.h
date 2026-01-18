// File: otr_builder.h
#pragma once

#include <vector>
#include <string>
#include "otr_generator.h"
#include <android/asset_manager.h>

// Forward declaration
struct RomInfo;

class OTRBuilder {
public:
    // --- Asset-based OTR generation (Android) ---
    static bool buildOTRForROM(AAssetManager* mgr,
                               const uint8_t* romData,
                               size_t romSize,
                               std::vector<uint8_t>& outOTR) 
    {
        RomInfo info{};
        if (!OTRGenerator::detectRomVersion(romData, romSize, info)) return false;

        std::string yamlFile;
        if (info.version == "USv1.0") yamlFile = "otr_yaml/decompressed.us.v10.yaml";
        else if (info.version == "PAL") yamlFile = "otr_yaml/decompressed.pal.yaml";
        else return false;

        std::vector<uint8_t> yamlBuf = OTRGenerator::loadYAMLAsset(mgr, yamlFile.c_str());
        if (yamlBuf.empty()) return false;

        OTRGenerator gen;
        return gen.generateOTR(romData, romSize,
                               reinterpret_cast<const char*>(yamlBuf.data()),
                               yamlBuf.size(),
                               outOTR);
    }

    // --- Direct in-memory OTR generation ---
    static bool buildBKOTR(const uint8_t* romData,
                           size_t romSize,
                           const char* yamlData,
                           size_t yamlSize,
                           std::vector<uint8_t>& outOTR);
};