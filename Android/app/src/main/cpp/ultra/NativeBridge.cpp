#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

static jobject g_callbackObj = nullptr; // Now points to the Service
static jmethodID g_updateProgressMid = nullptr;

extern "C" {

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    otr_builder_set_jvm(vm); 
    return JNI_VERSION_1_6;
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject callbackTarget) {
    if (g_callbackObj != nullptr) {
        env->DeleteGlobalRef(g_callbackObj);
    }
    // callbackTarget is the OtrService instance
    g_callbackObj = env->NewGlobalRef(callbackTarget);

    jclass serviceClass = env->GetObjectClass(g_callbackObj);
    g_updateProgressMid = env->GetMethodID(serviceClass, "updateOtrProgress", "(ILjava/lang/String;)V");

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Bridge linked to Service");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz,
                                                jint romFd, jobject assetManager, jstring outputDir) {
    if (g_callbackObj == nullptr) return;

    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);

    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        uint32_t manifestSize = (uint32_t)AAsset_getLength(asset);

        run_native_otr_generation_with_callback(env, g_callbackObj, g_updateProgressMid,
                                              romFd, manifestBuffer, manifestSize, outDir);
        AAsset_close(asset);
    }
    env->ReleaseStringUTFChars(outputDir, outDir);
}

}
