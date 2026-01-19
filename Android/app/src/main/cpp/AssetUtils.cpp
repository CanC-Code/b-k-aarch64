#include "AssetUtils.hpp"
#include <android/asset_manager_jni.h>
#include <android/log.h>

#define LOG_TAG "ASSET_UTILS"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

std::vector<uint8_t> readAsset(AAssetManager* mgr, const char* path) {
    AAsset* asset = AAssetManager_open(mgr, path, AASSET_MODE_BUFFER);
    if (!asset) {
        LOGI("Failed to open asset: %s", path);
        return {};
    }
    size_t size = AAsset_getLength(asset);
    std::vector<uint8_t> buffer(size);
    AAsset_read(asset, buffer.data(), size);
    AAsset_close(asset);
    return buffer;
}