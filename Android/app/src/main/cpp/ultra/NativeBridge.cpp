#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

[span_4](start_span)static jobject g_mainActivityObj = nullptr;[span_4](end_span)
[span_5](start_span)static jmethodID g_updateProgressMid = nullptr;[span_5](end_span)

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject activity) {
    if (g_mainActivityObj != nullptr) {
        [span_6](start_span)env->DeleteGlobalRef(g_mainActivityObj);[span_6](end_span)
    }
    [span_7](start_span)g_mainActivityObj = env->NewGlobalRef(activity);[span_7](end_span)
    [span_8](start_span)jclass activityClass = env->GetObjectClass(g_mainActivityObj);[span_8](end_span)
    // Matches the Java-side method updateOtrProgress(int, String)
    [span_9](start_span)g_updateProgressMid = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");[span_9](end_span)
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, 
                                                jint romFd, 
                                                jobject assetManager, 
                                                jstring outputDir) {
    [span_10](start_span)const char* outDir = env->GetStringUTFChars(outputDir, nullptr);[span_10](end_span)
    [span_11](start_span)AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);[span_11](end_span)

    [span_12](start_span)AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);[span_12](end_span)
    if (asset) {
        [span_13](start_span)uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);[span_13](end_span)
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              [span_14](start_span)romFd, manifestBuffer, outDir);[span_14](end_span)
        [span_15](start_span)AAsset_close(asset);[span_15](end_span)
    } else {
        _[span_16](start_span)_android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Could not find manifest_us.bin");[span_16](end_span)
    }

    [span_17](start_span)env->ReleaseStringUTFChars(outputDir, outDir);[span_17](end_span)
}

// Game Loop and Texture Implementations (Stubs)
[span_18](start_span)JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv* env, jclass clazz) { }[span_18](end_span)
[span_19](start_span)JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv* env, jclass clazz) { }[span_19](end_span)
[span_20](start_span)JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv* env, jclass clazz) { }[span_20](end_span)
[span_21](start_span)JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv* env, jclass clazz) { }[span_21](end_span)
JNIEXPORT jint JNICALL Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv* env, jclass clazz) { return 0; [span_22](start_span)}
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv* env, jclass clazz, jint tid) { }[span_22](end_span)

} // extern "C"
