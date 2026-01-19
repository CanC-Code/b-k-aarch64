#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>

#define LOG_TAG "OTR_ASSETS"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

struct EmbeddedAsset {
    const char* name;
    std::vector<uint8_t> data;
};

// Load a YAML asset from Android assets folder
inline std::vector<uint8_t> loadAsset(AAssetManager* mgr, const char* assetPath) {
    std::vector<uint8_t> buffer;
    if (!mgr || !assetPath) return buffer;

    AAsset* asset = AAssetManager_open(mgr, assetPath, AASSET_MODE_STREAMING);
    if (!asset) {
        LOGE("Failed to open asset: %s", assetPath);
        return buffer;
    }

    off_t size = AAsset_getLength(asset);
    if (size <= 0) {
        LOGE("Empty asset: %s", assetPath);
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

// Convenience function to load all OTR YAMLs
inline std::vector<EmbeddedAsset> loadEmbeddedOTRAssets(AAssetManager* mgr) {
    return {
        {"pal", loadAsset(mgr, "otr_yaml/decompressed.pal.yaml")},
        {"us.v10", loadAsset(mgr, "otr_yaml/decompressed.us.v10.yaml")}
    };
}