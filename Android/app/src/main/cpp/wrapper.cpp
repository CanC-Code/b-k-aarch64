// File: wrapper.cpp
// Author: CCVO
// Purpose: JNI wrapper for alternate OTR generation
// Copyright: CanC-code - CCVO

#include <jni.h>
#include <android/log.h>
#include <android/asset_manager_jni.h>
#include "AssetUtils.hpp" // << include the shared readAsset

#define LOG_TAG "NativeWrapper"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// JNI method to generate OTR content from alternate wrapper
extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeWrapper_generateOTR(JNIEnv* env, jobject thiz, jobject assetManager) {
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    if (!mgr) {
        LOGI("Failed to get AAssetManager from Java");
        return;
    }

    // Example usage of readAsset (now from AssetUtils.hpp)
    std::vector<uint8_t> palData = readAsset(mgr, "embedded_pal.yaml");
    std::vector<uint8_t> usData  = readAsset(mgr, "embedded_us.yaml");

    LOGI("Wrapper OTR asset sizes: PAL=%zu, US=%zu", palData.size(), usData.size());

    // TODO: alternate OTR generation logic here
}