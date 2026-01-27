#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

static jobject g_mainActivityObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;

// Initialize the Global JVM pointer for thread callbacks to prevent crashes in background threads
JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    otr_builder_set_jvm(vm); [span_2](start_span)[span_3](start_span)//[span_2](end_span)[span_3](end_span)
    return JNI_VERSION_1_6;
}

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject activity) {
    if (g_mainActivityObj != nullptr) {
        env->DeleteGlobalRef(g_mainActivityObj); [span_4](start_span)//[span_4](end_span)
    }
    // Store a global reference to the activity to use for callbacks later
    g_mainActivityObj = env->NewGlobalRef(activity); [span_5](start_span)//[span_5](end_span)
    jclass activityClass = env->GetObjectClass(g_mainActivityObj);
    
    // Cache the method ID for updateOtrProgress(int, String)
    g_updateProgressMid = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V"); [span_6](start_span)//[span_6](end_span)
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, 
                                                jint romFd, 
                                                jobject assetManager, 
                                                jstring outputDir) {
    const char* outDir = env->GetStringUTFChars(outputDir, nullptr); [span_7](start_span)//[span_7](end_span)
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager); [span_8](start_span)//[span_8](end_span)

    // Open the manifest asset required for OTR generation
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER); [span_9](start_span)//[span_9](end_span)
    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset); [span_10](start_span)//[span_10](end_span)
        
        // This call will now have access to g_jvm initialized in JNI_OnLoad for thread safety
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              romFd, manifestBuffer, outDir); [span_11](start_span)//[span_11](end_span)
        AAsset_close(asset); [span_12](start_span)//[span_12](end_span)
    } else {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Could not find manifest_us.bin"); [span_13](start_span)//[span_13](end_span)
    }

    env->ReleaseStringUTFChars(outputDir, outDir); [span_14](start_span)//[span_14](end_span)
}

// Stub implementations for game loop controls
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv* env, jclass clazz) { 
    // Logic to start the game loop would go here
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv* env, jclass clazz) { 
    // Logic to pause the game loop
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv* env, jclass clazz) { 
    // Logic to resume the game loop
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv* env, jclass clazz) { 
    // Logic to clean up resources
}

[span_15](start_span)// These methods were added back to match the Java NativeBridge declarations[span_15](end_span)
JNIEXPORT jint JNICALL Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv* env, jclass clazz) { 
    return 0; [span_16](start_span)// Return a default texture ID or handle[span_16](end_span)
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv* env, jclass clazz, jint tid) { 
    // Logic to update the texture with the given ID
}

} // extern "C"
