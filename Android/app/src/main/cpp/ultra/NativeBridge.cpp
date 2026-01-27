#include <jni.h>
#include <unistd.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

// Globals to store JNI state
static jobject g_mainActivityObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;

extern "C" {

// Initialize the bridge and capture the Activity reference
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject activity) {
    if (g_mainActivityObj != nullptr) {
        env->DeleteGlobalRef(g_mainActivityObj);
    }
    
    // Create GlobalRef so the activity reference doesn't expire during background tasks
    g_mainActivityObj = env->NewGlobalRef(activity);
    
    jclass activityClass = env->GetObjectClass(g_mainActivityObj);
    
    // Find updateOtrProgress(int, String) - matches your MainActivity.java
    g_updateProgressMid = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");
    
    if (g_updateProgressMid == nullptr) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Could not find updateOtrProgress method!");
    }
}

// Run the OTR generation logic
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, 
                                                jint romFd, jobject assetManager, 
                                                jstring outputDir) {
    
    // Duplicate the FD so the native side keeps access if Java closes the original
    int nativeFd = dup(romFd); 
    if (nativeFd == -1) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Failed to duplicate ROM FD");
        return;
    }

    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    
    // Load the conversion manifest from APK assets
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        
        // This calls the builder logic defined in otr_builder.cpp
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              nativeFd, manifestBuffer, outDir);
        AAsset_close(asset);
    }
    
    close(nativeFd);
    env->ReleaseStringUTFChars(outputDir, outDir);
}

// Stubs for game loop and rendering to satisfy NativeBridge.java definitions
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv* env, jclass clazz) {}
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv* env, jclass clazz) {}
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv* env, jclass clazz) {}
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv* env, jclass clazz) {}
JNIEXPORT jint JNICALL Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv* env, jclass clazz) { return 0; }
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv* env, jclass clazz, jint tid) {}

} // extern "C"
