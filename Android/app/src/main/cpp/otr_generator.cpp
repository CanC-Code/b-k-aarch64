// OTRGenerator.cpp
#include "OTRGenerator.hpp"
#include <android/log.h>
#include <cstring>

#define LOG_TAG "OTR_GEN"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

std::vector<uint8_t> OTRGenerator::loadYAMLAsset(const char* assetPath) {
    std::vector<uint8_t> buffer;
    if (!assetManager || !assetPath) return buffer;

    AAsset* asset = AAssetManager_open(assetManager, assetPath, AASSET_MODE_STREAMING);
    if (!asset) {
        LOGE("Failed to open YAML asset: %s", assetPath);
        return buffer;
    }

    off_t size = AAsset_getLength(asset);
    if (size <= 0) { AAsset_close(asset); return buffer; }

    buffer.resize(size);
    int read = AAsset_read(asset, buffer.data(), size);
    if (read != size) {
        LOGE("Failed to read full YAML asset: %s", assetPath);
        buffer.clear();
    }

    AAsset_close(asset);
    return buffer;
}

bool OTRGenerator::generateOTR(const uint8_t* romData, size_t romSize,
                               const char* yamlAssetPath) {
    if (!romData || romSize == 0 || !yamlAssetPath) return false;

    auto yamlData = loadYAMLAsset(yamlAssetPath);
    if (yamlData.empty()) return false;

    outOTR.clear();
    outOTR.reserve(romSize + yamlData.size());

    // Simple interleave simulation with progress
    const size_t totalSteps = 100;
    size_t chunkROM = romSize / totalSteps;
    size_t chunkYAML = yamlData.size() / totalSteps;

    for (size_t step = 0; step < totalSteps; ++step) {
        size_t romStart = step * chunkROM;
        size_t romEnd = (step == totalSteps - 1) ? romSize : romStart + chunkROM;
        outOTR.insert(outOTR.end(), romData + romStart, romData + romEnd);

        size_t yamlStart = step * chunkYAML;
        size_t yamlEnd = (step == totalSteps - 1) ? yamlData.size() : yamlStart + chunkYAML;
        outOTR.insert(outOTR.end(), yamlData.begin() + yamlStart, yamlData.begin() + yamlEnd);

        reportProgress((step + 1) / float(totalSteps));
    }

    LOGI("OTR generation finished: %zu bytes", outOTR.size());
    return true;
}