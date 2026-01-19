#include "otr_generator.hpp"
#include <android/log.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>

#define LOG_TAG "OTRGenerator"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

std::vector<uint8_t> OTRGenerator::loadYAMLAsset(const char* assetName) {
    std::vector<uint8_t> buffer;
    if (!assetManager) return buffer;

    AAsset* asset = AAssetManager_open(assetManager, assetName, AASSET_MODE_BUFFER);
    if (!asset) {
        LOGI("Failed to open asset: %s", assetName);
        return buffer;
    }

    size_t size = AAsset_getLength(asset);
    buffer.resize(size);
    AAsset_read(asset, buffer.data(), size);
    AAsset_close(asset);

    return buffer;
}

bool OTRGenerator::generateOTR(const std::vector<uint8_t>& romData) {
    if (romData.empty()) return false;

    auto palYAML = loadYAMLAsset("otr_yaml/decompressed.pal.yaml");
    auto usYAML = loadYAMLAsset("otr_yaml/decompressed.us.v10.yaml");

    if (palYAML.empty() || usYAML.empty()) return false;

    // Runtime generation logic (placeholder)
    otrBuffer.clear();
    otrBuffer.insert(otrBuffer.end(), romData.begin(), romData.end());
    otrBuffer.insert(otrBuffer.end(), palYAML.begin(), palYAML.end());
    otrBuffer.insert(otrBuffer.end(), usYAML.begin(), usYAML.end());

    LOGI("Generated OTR (%zu bytes)", otrBuffer.size());
    return true;
}