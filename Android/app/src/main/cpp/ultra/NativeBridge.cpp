#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

static jobject g_mainActivityObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;

extern "C" {

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    otr_builder_set_jvm(vm); 
    return JNI_VERSION_1_6;
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject activity) {
    if (g_mainActivityObj != nullptr) {
        env->DeleteGlobalRef(g_mainActivityObj);
    }
    g_mainActivityObj = env->NewGlobalRef(activity);

    jclass activityClass = env->GetObjectClass(g_mainActivityObj);
    g_updateProgressMid = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");

    if (g_updateProgressMid == nullptr) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Failed to find updateOtrProgress method!");
    }

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "JNI Initialized");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz,
                                                jint romFd,
                                                jobject assetManager,
                                                jstring outputDir) {
    if (g_mainActivityObj == nullptr || g_updateProgressMid == nullptr) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "NativeBridge not initialized properly");
        return;
    }

    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (asset) {
        // Use a pointer cast to avoid ambiguity
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        uint32_t manifestSize = (uint32_t)AAsset_getLength(asset);

        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid,
                                              romFd, manifestBuffer, manifestSize, outDir);
        AAsset_close(asset);
    } else {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Manifest not found in assets");
    }

    env->ReleaseStringUTFChars(outputDir, outDir);
}

} // extern "C"
