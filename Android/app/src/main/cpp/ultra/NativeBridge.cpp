#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// 1. Include our 64-bit safe bridge
#include "n64_types.h"

// 2. Define the types libaudio.h is missing before we include it
typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];

// Trick the N64 headers into skipping redefinitions of hardware types
#define _GBI_H_      
#define _ABI_H_      
#define _OSTASK_H_   

extern "C" {
    #include <PR/libaudio.h>
}

#define LOG_TAG "BKA_NATIVE"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {
    void mainLoop(void);
    void ResourceMgr_Init(const char* otrPath, uint8_t* manifestBuf, uint32_t manifestSize);
}

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeGameBoot(JNIEnv* env, jclass clazz, jstring otrPath, jobject assetManager) {
    LOGI("Starting Banjo-Kazooie Native Boot Sequence...");

    // 1. Initialize N64 Audio Globals
    // alGlobals is declared as ALGlobals* in libaudio.h
    if (alGlobals == nullptr) {
        alGlobals = (ALGlobals*)malloc(8192); // 8KB for safety
        memset(alGlobals, 0, 8192);
        LOGI("Audio Globals Initialized.");
    }

    const char* cOtrPath = env->GetStringUTFChars(otrPath, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (asset) {
        uint8_t* buffer = (uint8_t*)AAsset_getBuffer(asset);
        uint32_t size = AAsset_getLength(asset);
        LOGI("Manifest found. Initializing Resource Manager...");
        ResourceMgr_Init(cOtrPath, buffer, size);
        AAsset_close(asset);
    }

    // 2. Start the game loop
    LOGI("Executing mainLoop...");
    mainLoop();

    env->ReleaseStringUTFChars(otrPath, cOtrPath);
}

}
