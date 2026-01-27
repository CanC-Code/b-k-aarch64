#include <jni.h>
#include <android/log.h>
#include <android/asset_manager_jni.h>
#include <stdlib.h> // Required for malloc and free
#include "ultra/otr_builder.h"

#define LOG_TAG "BKA_Wrapper"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// Forward declaration for the setter in otr_builder.cpp
extern void otr_builder_set_jvm(JavaVM* vm);

/**
 * JNI_OnLoad is called automatically when the native library is loaded.
 * We use it to capture the JavaVM pointer for later use in background threads.
 */
JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    LOGI("JNI_OnLoad: Initializing BKAWrapper Native Library");
    
    // Store the VM pointer globally for the OTR builder and other modules
    otr_builder_set_jvm(vm);
    
    return JNI_VERSION_1_6;
}

extern "C" {

/**
 * nativeInit: Global native setup called from Java.
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject context) {
    LOGI("NativeBridge: Global initialization");
}

/**
 * runOtrGeneration: Entry point for the OTR extraction process.
 * This function loads the manifest from assets and starts the extraction.
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, jint romFd, jobject assetManager, jstring outDir) {
    const char* nativeOutDir = env->GetStringUTFChars(outDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    LOGI("NativeBridge: Starting OTR Generation to %s", nativeOutDir);

    // 1. Load the manifest from the APK assets (using 'manifest_us.bin' based on project structure)
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (asset) {
        size_t size = AAsset_getLength(asset);
        uint8_t* buffer = (uint8_t*)malloc(size); // malloc is now declared
        AAsset_read(asset, buffer, size);
        AAsset_close(asset);

        // 2. Identify the Java callback method (updateOtrProgress)
        jmethodID progressMid = env->GetStaticMethodID(clazz, "updateOtrProgress", "(ILjava/lang/String;)V");

        // 3. Launch the extraction. The builder will use the stored JavaVM for background callbacks.
        run_native_otr_generation_with_callback(env, nullptr, progressMid, romFd, buffer, nativeOutDir);

        free(buffer); // free is now declared
    } else {
        LOGI("NativeBridge: Failed to open manifest_us.bin from assets!");
    }

    env->ReleaseStringUTFChars(outDir, nativeOutDir);
}

/**
 * Game Loop and Texture stubs for NativeBridge.
 */
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv* env, jclass clazz) {
    LOGI("NativeBridge: Start Game Loop");
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv* env, jclass clazz) {
    LOGI("NativeBridge: Pause Game Loop");
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv* env, jclass clazz) {
    LOGI("NativeBridge: Resume Game Loop");
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv* env, jclass clazz) {
    LOGI("NativeBridge: Cleanup");
}

JNIEXPORT jint JNICALL Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv* env, jclass clazz) { 
    return 0; 
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv* env, jclass clazz, jint tid) {
    // Logic to push native frame buffer to OpenGL texture
}

} // extern "C"
