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
static JavaVM* g_jvm = nullptr;

extern "C" {

// Called from MainActivity.onCreate via NativeBridge.nativeInit(this)
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject activity) {
    // 1. Store the JVM (crucial for background thread callbacks)
    env->GetJavaVM(&g_jvm);
    otr_builder_set_jvm(g_jvm); 
    
    // 2. Create a persistent reference to the Activity
    if (g_mainActivityObj != nullptr) {
        env->DeleteGlobalRef(g_mainActivityObj);
    }
    g_mainActivityObj = env->NewGlobalRef(activity);
    
    // 3. Find the method ID (Matching MainActivity.java: updateOtrProgress)
    jclass activityClass = env->GetObjectClass(activity);
    g_updateProgressMid = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");
    
    if (g_updateProgressMid == nullptr) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "CRITICAL: Could not find updateOtrProgress method!");
    }
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, 
                                                jint romFd, 
                                                jobject assetManager, 
                                                jstring outputDir) {
    
    // Safety check: ensure init was called
    if (g_mainActivityObj == nullptr || g_updateProgressMid == nullptr) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "runOtrGeneration called before nativeInit!");
        return;
    }

    // Duplicate FD so the background thread maintains access
    int nativeFd = dup(romFd); 
    if (nativeFd == -1) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Failed to dup ROM FD");
        return;
    }

    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        
        // Matches the signature in your provided otr_builder.h
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              nativeFd, manifestBuffer, outDir);
        AAsset_close(asset);
    }

    close(nativeFd); 
    env->ReleaseStringUTFChars(outputDir, outDir);
}

// Stub implementations for game loop and textures
JNIEXPORT jint JNICALL Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv* env, jclass clazz) { return 0; }
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv* env, jclass clazz, jint tid) {}
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv* env, jclass clazz) {}
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv* env, jclass clazz) {}
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv* env, jclass clazz) {}
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv* env, jclass clazz) {}

} // extern "C"
