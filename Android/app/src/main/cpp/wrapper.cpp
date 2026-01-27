#include <jni.h>
#include <android/log.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <string>
#include "ultra/otr_builder.h"

#define LOG_TAG "BKAWrapper"

static JavaVM* g_vm = nullptr;
static jobject g_mainActivityObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;

// JNI_OnLoad is only defined here, so it's safe.
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    g_vm = vm;
    return JNI_VERSION_1_6;
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jobject thiz, jobject activity, jobject assetManager, jstring outputDir) {
    g_mainActivityObj = env->NewGlobalRef(activity);
    
    jclass clazz = env->GetObjectClass(activity);
    g_updateProgressMid = env->GetMethodID(clazz, "updateProgress", "(I)V");

    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    // Load the binary manifest generated from your assets.yaml
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    
    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        
        // This calls the actual logic in ultra/otr_builder.cpp
        // Assuming romFd is handled or passed elsewhere, 
        // or add a parameter if your Java side sends the FD.
        int romFd = -1; 
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              romFd, manifestBuffer, outDir);
        
        AAsset_close(asset);
    } else {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Could not find manifest_us.bin in assets");
    }

    env->ReleaseStringUTFChars(outputDir, outDir);
}

/** * DUPLICATE SYMBOLS REMOVED:
 * The following functions have been removed from this file because they are 
 * already implemented in ultra/NativeBridge.cpp:
 * - startGameLoop
 * - pauseGameLoop
 * - resumeGameLoop
 * - cleanupGame
 * - initTexture
 * - updateTexture
 */
