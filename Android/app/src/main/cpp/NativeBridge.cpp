#include <jni.h>
#include "otr_generator.hpp"
#include <vector>
#include <android/asset_manager_jni.h>
#include <android/log.h>

#define LOG_TAG "NATIVE_BRIDGE"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// Remove readAsset from extern "C"
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

extern "C" {

JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_generateOTR(JNIEnv* env, jobject thiz, jobject assetManager) {
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    if (!mgr) return JNI_FALSE;

    OTRGenerator generator; // default constructor

    auto palData = readAsset(mgr, "otr_yaml/decompressed.pal.yaml");
    auto usData  = readAsset(mgr, "otr_yaml/decompressed.us.v10.yaml");

    generator.loadYAML("pal", palData.data(), palData.size());
    generator.loadYAML("us.v10", usData.data(), usData.size());

    std::vector<uint8_t> outPal;
    std::vector<uint8_t> outUS;

    bool success1 = generator.generate("pal", outPal);
    bool success2 = generator.generate("us.v10", outUS);

    return (success1 && success2) ? JNI_TRUE : JNI_FALSE;
}

}