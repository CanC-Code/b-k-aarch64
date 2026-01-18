#include "otr_builder.h"
#include <string>
#include <cstring>
#include <android/log.h>

#define LOG_TAG "BK_OTR"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

bool buildOTRForROM(
    AAssetManager* mgr,
    const uint8_t* romData,
    size_t romSize,
    std::vector<uint8_t>& outOTR,
    ProgressCallback progress
) {
    OTRGenerator::RomInfo info{};
    if (!OTRGenerator::detectRomVersion(romData, romSize, info)) {
        LOGE("ROM detection failed");
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
                      outOTR,
                      progress);
}

bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    const char* yamlData,
    size_t yamlSize,
    std::vector<uint8_t>& outOTR,
    ProgressCallback progress
) {
    if (!romData || romSize == 0 || !yamlData || yamlSize == 0) {
        LOGE("Invalid input to buildBKOTR");
        return false;
    }

    OTRGenerator gen;

    // Set up a progress wrapper if provided
    gen.setProgressCallback([&progress](float p) {
        if (progress) progress(p);  // forward to caller
    });

    bool ok = gen.generateOTR(romData, romSize, yamlData, yamlSize, outOTR);
    if (!ok) {
        LOGE("generateOTR failed");
        return false;
    }

    LOGI("OTR build complete: %zu bytes", outOTR.size());
    return true;
}