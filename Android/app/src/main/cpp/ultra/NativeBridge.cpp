#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

static jobject g_mainActivityObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    otr_builder_set_jvm(vm); 
    return JNI_VERSION_1_6;
}

extern "C" {

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject activity) {
    if (g_mainActivityObj != nullptr) {
        env->DeleteGlobalRef(g_mainActivityObj);
    }
    g_mainActivityObj = env->NewGlobalRef(activity);

    jclass activityClass = env->GetObjectClass(g_mainActivityObj);
    g_updateProgressMid = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "JNI initialized");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz,
                                                jint romFd,
                                                jobject assetManager,
                                                jstring outputDir) {
    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    // FIX: manifest_us.bin is a binary file; we must get its length
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        off_t manifestSize = AAsset_getLength(asset);

        __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Starting OTR with size: %ld", manifestSize);

        // Pass manifestSize so the loop in otr_builder.cpp knows when to stop
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid,
                                              romFd, manifestBuffer, (uint32_t)manifestSize, outDir);
        AAsset_close(asset);
    } else {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "COULD NOT OPEN MANIFEST");
    }

    env->ReleaseStringUTFChars(outputDir, outDir);
}

}
