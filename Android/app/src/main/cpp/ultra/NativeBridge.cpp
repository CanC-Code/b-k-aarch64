#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// Include our N64 bridge to get the 64-bit safe types
#include "n64_types.h"

// MACRO SHIELD: Prevent C++ from choking on N64 header redefinitions
#define Gfx __Gfx_ignore
#define Acmd __Acmd_ignore
#define ALDMANew __ALDMANew_ignore

extern "C" {
    #include <PR/libaudio.h>
}

// Remove the shield so we can use the 64-bit types normally
#undef Gfx
#undef Acmd
#undef ALDMANew

#define LOG_TAG "BKA_NATIVE"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {
    void mainLoop(void);
    void ResourceMgr_Init(const char* otrPath, uint8_t* manifestBuf, uint32_t manifestSize);
    
    // OPAQUE POINTER: Link to the C engine's global audio pointer without needing the struct
    extern void* alGlobals;
}

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeGameBoot(JNIEnv* env, jclass clazz, jstring otrPath, jobject assetManager) {
    LOGI("Starting Banjo-Kazooie Native Boot Sequence...");

    // 1. Initialize N64 Audio Globals using a raw block of memory
    if (alGlobals == nullptr) {
        alGlobals = malloc(4096); // 4KB is safely larger than the N64 ALGlobals struct
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

    // 2. Start the game. 
    // mainLoop usually never returns in N64 games (it's the infinite game loop)
    LOGI("Executing mainLoop...");
    mainLoop();

    env->ReleaseStringUTFChars(otrPath, cOtrPath);
}

}
