// File: NativeBridge.cpp
// Author: CCVO
// Purpose: JNI bridge for generating OTR content
// Copyright: CanC-code - CCVO

#include <jni.h>
#include <android/log.h>
#include <android/asset_manager_jni.h>
#include "AssetUtils.hpp" // << include the shared readAsset

#define LOG_TAG "NativeBridge"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// JNI method to generate OTR content
extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_generateOTR(JNIEnv* env, jobject thiz, jobject assetManager) {
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    if (!mgr) {
        LOGI("Failed to get AAssetManager from Java");
        return;
    }

    // Example usage of readAsset (now from AssetUtils.hpp)
    std::vector<uint8_t> palData = readAsset(mgr, "embedded_pal.yaml");
    std::vector<uint8_t> usData  = readAsset(mgr, "embedded_us.yaml");

    LOGI("OTR asset sizes: PAL=%zu, US=%zu", palData.size(), usData.size());

    // TODO: actual OTR generation logic here
}