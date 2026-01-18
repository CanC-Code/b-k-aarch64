#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <vector>
#include <cstdint>
#include <string>
#include <android/log.h>

#define LOG_TAG "OTR_GEN"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// mgr must be AAssetManager*
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