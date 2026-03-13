#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// 1. Include our 64-bit safe bridge first
#include "n64_types.h"

// 2. Trick the N64 headers into thinking these types are already handled
// These macros are often used as guards in the original SDK headers
#define _GBI_H_      // Blocks gbi.h redefinitions
#define _ABI_H_      // Blocks abi.h redefinitions
#define _OSTASK_H_   // Blocks sptask.h redefinitions

extern "C" {
    // We only want the audio function declarations, not the base types
    #include <PR/libaudio.h>
}

#define LOG_TAG "BKA_NATIVE"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {
    void mainLoop(void);
    void ResourceMgr_Init(const char* otrPath, uint8_t* manifestBuf, uint32_t manifestSize);
    
    // The engine's global audio pointer
    extern void* alGlobals;
}

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeGameBoot(JNIEnv* env, jclass clazz, jstring otrPath, jobject assetManager) {
    LOGI("Starting Banjo-Kazooie Native Boot Sequence...");

    // 1. Initialize N64 Audio Globals
    if (alGlobals == nullptr) {
        alGlobals = malloc(4096); 
        memset(alGlobals, 0, 4096);
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
