#include <jni.h>
#include <unistd.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

// 1. DEFINE THE MISSING GLOBALS
static jobject g_mainActivityObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;
static JavaVM* g_jvm = nullptr;

// 2. ADD THE INIT FUNCTION
// This must be called from Java (e.g., in MainActivity's onCreate)
extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initNative(JNIEnv* env, jclass clazz, jobject activity) {
    env->GetJavaVM(&g_jvm);
    g_mainActivityObj = env->NewGlobalRef(activity);
    
    jclass activityClass = env->GetObjectClass(activity);
    g_updateProgressMid = env->GetMethodID(activityClass, "onOtrProgress", "(ILjava/lang/String;)V");
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, 
                                                jint romFd, 
                                                jobject assetManager, 
                                                jstring outputDir) {
    
    int nativeFd = dup(romFd); 
    if (nativeFd == -1) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Failed to dup FD");
        return;
    }

    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        
        // These identifiers are now declared and will compile
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              nativeFd, manifestBuffer, outDir);
        AAsset_close(asset);
    }

    close(nativeFd); 
    env->ReleaseStringUTFChars(outputDir, outDir);
}
