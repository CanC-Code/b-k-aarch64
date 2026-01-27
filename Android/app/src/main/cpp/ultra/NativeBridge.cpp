#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

static jobject g_mainActivityObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;

// Initialize the Global JVM pointer for thread callbacks
JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void* reserved) {
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
        // This will now have access to g_jvm initialized in JNI_OnLoad
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              romFd, manifestBuffer, outDir);
        AAsset_close(asset);
    } else {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Could not find manifest_us.bin");
    }

    env->ReleaseStringUTFChars(outputDir, outDir);
}

JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv* env, jclass clazz) { }
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv* env, jclass clazz) { }
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv* env, jclass clazz) { }
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv* env, jclass clazz) { }
JNIEXPORT jint JNICALL Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv* env, jclass clazz) { return 0; }
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv* env, jclass clazz, jint tid) { }

} // extern "C"
