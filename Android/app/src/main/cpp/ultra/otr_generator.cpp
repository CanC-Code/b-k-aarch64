#include "otr_generator.hpp"
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <cstring>
#include <stdexcept>
#include <android/log.h>

#define LOG_TAG "OTR_GEN"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Detect ROM version
bool OTRGenerator::detectRomVersion(const uint8_t* romData, size_t romSize, RomInfo& outInfo) {
    if (romSize >= 4) {
        if (romData[0] == 'U') outInfo.version = "USv1.0";
        else if (romData[0] == 'P') outInfo.version = "PAL";
        else return false;
        return true;
    }
    return false;
}

// Load YAML asset from Android assets
std::vector<uint8_t> OTRGenerator::loadYAMLAsset(void* mgr, const char* assetPath) {
    std::vector<uint8_t> buffer;

    if (!mgr || !assetPath) {
        LOGE("Invalid asset manager or path");
        return buffer;
    }

    AAssetManager* assetManager = static_cast<AAssetManager*>(mgr);
    AAsset* asset = AAssetManager_open(assetManager, assetPath, AASSET_MODE_STREAMING);
    if (!asset) {
        LOGE("Failed to open asset: %s", assetPath);
        return buffer;
    }

    off_t size = AAsset_getLength(asset);
    if (size <= 0) {
        LOGE("Empty or invalid asset: %s", assetPath);
        AAsset_close(asset);
        return buffer;
    }

    buffer.resize(size);
    int read = AAsset_read(asset, buffer.data(), size);
    if (read != size) {
        LOGE("Failed to read full asset: %s (read %d of %ld)", assetPath, read, size);
        buffer.clear();
    }

    AAsset_close(asset);
    return buffer;
}

// Generate OTR from ROM + YAML
bool OTRGenerator::generateOTR(
        const uint8_t* romData,
        size_t romSize,
        const char* yamlData,
        size_t yamlSize,
        std::vector<uint8_t>& outOTR
) {
    if (!romData || !yamlData) return false;

    size_t totalSteps = 100; // fake progress steps
    outOTR.clear();
    outOTR.reserve(romSize + yamlSize);

    for (size_t i = 0; i < totalSteps; ++i) {
        float progress = static_cast<float>(i) / static_cast<float>(totalSteps);
        reportProgress(progress);
    }

    outOTR.insert(outOTR.end(), romData, romData + romSize);
    outOTR.insert(outOTR.end(), yamlData, yamlData + yamlSize);

    reportProgress(1.0f);
    return true;
}