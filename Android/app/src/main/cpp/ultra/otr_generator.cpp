// File: otr_builder.cpp
#include "otr_builder.h"
#include "ultra/otr_generator.h"
#include <android/log.h>
#include <android/asset_manager.h>

#define LOG_TAG "OTR_BUILDER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ---------------------------------------------------------------------
// In-memory OTR generation
// ---------------------------------------------------------------------
bool OTRBuilder::buildBKOTR(const uint8_t* romData,
                            size_t romSize,
                            const char* yamlData,
                            size_t yamlSize,
                            std::vector<uint8_t>& outOTR)
{
    outOTR.clear();
    if (!romData || romSize == 0 || !yamlData || yamlSize == 0) {
        LOGE("Invalid input to buildBKOTR");
        return false;
    }

    OTRGenerator gen;
    bool success = gen.generateOTR(romData, romSize, yamlData, yamlSize, outOTR);
    if (!success) {
        LOGE("OTRGenerator failed");
        return false;
    }

    LOGI("OTR generated in-memory, size: %zu bytes", outOTR.size());
    return true;
}

// ---------------------------------------------------------------------
// Android asset-based OTR generation
// ---------------------------------------------------------------------
bool OTRBuilder::buildOTRForROM(AAssetManager* mgr,
                                const uint8_t* romData,
                                size_t romSize,
                                std::vector<uint8_t>& outOTR)
{
    if (!mgr || !romData || romSize == 0) {
        LOGE("Invalid input to buildOTRForROM");
        return false;
    }

    RomInfo info{};
    if (!OTRGenerator::detectRomVersion(romData, romSize, info)) {
        LOGE("ROM version detection failed");
        return false;
    }

    std::string yamlFile;
    if (info.version == "USv1.0") yamlFile = "otr_yaml/decompressed.us.v10.yaml";
    else if (info.version == "PAL") yamlFile = "otr_yaml/decompressed.pal.yaml";
    else {
        LOGE("Unsupported ROM version: %s", info.version.c_str());
        return false;
    }

    std::vector<uint8_t> yamlBuf = OTRGenerator::loadYAMLAsset(mgr, yamlFile.c_str());
    if (yamlBuf.empty()) {
        LOGE("Failed to load YAML asset: %s", yamlFile.c_str());
        return false;
    }

    return buildBKOTR(romData, romSize,
                      reinterpret_cast<const char*>(yamlBuf.data()),
                      yamlBuf.size(),
                      outOTR);
}