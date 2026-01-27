#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

static jobject g_mainActivityObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject activity) {
    g_mainActivityObj = env->NewGlobalRef(activity);
    jclass activityClass = env->GetObjectClass(g_mainActivityObj);
    g_updateProgressMid = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, 
                                                jint romFd, 
                                                jobject assetManager, 
                                                jstring outputDir) {
    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    // Open manifest from Android assets
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        
        // Orchestrator call
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              romFd, manifestBuffer, outDir);
        AAsset_close(asset);
    } else {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Could not find manifest_us.bin in assets");
    }

    env->ReleaseStringUTFChars(outputDir, outDir);
}

// Note: startGameLoop, initTexture, etc. are NOT defined here to avoid duplicate symbol errors.
// They are provided by wrapper.cpp or other linked sources.

} // extern "C"
