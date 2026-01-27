#include <jni.h>
#include <android/log.h>
#include <android/asset_manager_jni.h>
#include "ultra/otr_builder.h"

#define LOG_TAG "BKA_Wrapper"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// Forward declaration of the setter in otr_builder.cpp
extern void otr_builder_set_jvm(JavaVM* vm);

/**
 * Single JNI_OnLoad for the entire library.
 * This is called automatically by the system when System.loadLibrary("bkawrapper") is executed.
 */
JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    LOGI("JNI_OnLoad: Initializing BKAWrapper Native Library");
    
    // Pass the VM pointer to the OTR builder module for thread attachment
    otr_builder_set_jvm(vm);
    
    return JNI_VERSION_1_6;
}

extern "C" {

/**
 * nativeInit: Handles any global native setup.
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject context) {
    LOGI("NativeBridge: Global initialization");
    // Setup global native state here if necessary
}

/**
 * runOtrGeneration: Entry point for the OTR extraction process.
 * Called from OtrService.java.
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, jint romFd, jobject assetManager, jstring outDir) {
    const char* nativeOutDir = env->GetStringUTFChars(outDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    LOGI("NativeBridge: Starting OTR Generation to %s", nativeOutDir);

    // 1. Load the manifest from the APK assets
    AAsset* asset = AAssetManager_open(mgr, "manifest.bin", AASSET_MODE_BUFFER);
    if (asset) {
        size_t size = AAsset_getLength(asset);
        uint8_t* buffer = (uint8_t*)malloc(size);
        AAsset_read(asset, buffer, size);
        AAsset_close(asset);

        // 2. Identify the Java callback method (updateOtrProgress)
        // Note: clazz is NativeBridge. We need the activity/context if calling a non-static method,
        // but here we are using the static NativeBridge logic.
        jmethodID progressMid = env->GetStaticMethodID(clazz, "updateOtrProgress", "(ILjava/lang/String;)V");

        // 3. Launch the multithreaded extraction
        run_native_otr_generation_with_callback(env, nullptr, progressMid, romFd, buffer, nativeOutDir);

        free(buffer);
    } else {
        LOGI("NativeBridge: Failed to open manifest.bin from assets!");
    }

    env->ReleaseStringUTFChars(outDir, nativeOutDir);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv* env, jclass clazz) {
    LOGI("NativeBridge: Start Game Loop");
    // Implementation for starting the emulator engine
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv* env, jclass clazz) {
    LOGI("NativeBridge: Pause Game Loop");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv* env, jclass clazz) {
    LOGI("NativeBridge: Resume Game Loop");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv* env, jclass clazz) {
    LOGI("NativeBridge: Cleanup");
}

// STUBS for GLRenderer compatibility
JNIEXPORT jint JNICALL
Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv* env, jclass clazz) {
    return 0; 
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv* env, jclass clazz, jint tid) {
    // Logic to push native frame buffer to OpenGL texture
}

} // extern "C"
