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
    // Vital: NewGlobalRef prevents the activity from being GC'd while we use it
    g_mainActivityObj = env->NewGlobalRef(activity);

    jclass activityClass = env->GetObjectClass(g_mainActivityObj);
    // Find the updateOtrProgress method on the MainActivity
    g_updateProgressMid = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");
    
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "JNI initialized with GlobalRef");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz,
                                                jint romFd,
                                                jobject assetManager,
                                                jstring outputDir) {
    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid,
                                              romFd, manifestBuffer, outDir);
        AAsset_close(asset);
    }

    env->ReleaseStringUTFChars(outputDir, outDir);
}

}
