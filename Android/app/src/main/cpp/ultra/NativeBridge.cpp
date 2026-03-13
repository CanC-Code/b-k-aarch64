#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

// 1. Include our 64-bit safe bridge first to establish types
#include "n64_types.h"

// 2. Trick the N64 headers into skipping redefinitions of hardware types
// This ensures our 64-bit safe versions of Gfx, Acmd, etc., stay active.
#define _GBI_H_      
#define _ABI_H_      
#define _OSTASK_H_   

extern "C" {
    // libaudio.h now uses our scrubbed types and correct linkage
    #include <PR/libaudio.h>
    #include <PR/os.h>
}

#define LOG_TAG "BKA_NATIVE"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {
    // These functions are defined in core1/core2 of the decompilation
    void mainLoop(void);
    void ResourceMgr_Init(const char* otrPath, uint8_t* manifestBuf, uint32_t manifestSize);
}

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeGameBoot(JNIEnv* env, jclass clazz, jstring otrPath, jobject assetManager) {
    LOGI("Starting Banjo-Kazooie Native Boot Sequence...");

    // 1. Initialize N64 Audio Globals
    // We use the pointer declared in the SDK header, but allocate a safe 64-bit block
    if (alGlobals == nullptr) {
        alGlobals = (ALGlobals*)malloc(8192); 
        if (alGlobals != nullptr) {
            memset(alGlobals, 0, 8192);
            LOGI("Audio Globals Initialized.");
        } else {
            LOGI("CRITICAL ERROR: Failed to allocate memory for Audio Globals.");
            return;
        }
    }

    const char* cOtrPath = env->GetStringUTFChars(otrPath, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    // Load the OTR manifest from Android Assets
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (asset) {
        uint8_t* buffer = (uint8_t*)AAsset_getBuffer(asset);
        uint32_t size = AAsset_getLength(asset);
        LOGI("Manifest found. Initializing Resource Manager...");
        ResourceMgr_Init(cOtrPath, buffer, size);
        AAsset_close(asset);
    } else {
        LOGI("WARNING: manifest_us.bin not found in assets!");
    }

    // 2. Hand over control to the N64 Main Loop
    // This call normally does not return until the app is closed.
    LOGI("Executing mainLoop...");
    mainLoop();

    env->ReleaseStringUTFChars(otrPath, cOtrPath);
}

}
