#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include "otr_builder.h"

static jobject g_mainActivityObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject activity) {
    // Save global reference to MainActivity to call UI updates later
    g_mainActivityObj = env->NewGlobalRef(activity);
    jclass activityClass = env->GetObjectClass(g_mainActivityObj);
    g_updateProgressMid = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");
}

// Callback used by the OTR Builder to talk to Java
void send_progress_to_java(int percent, const char* fileName) {
    if (!g_mainActivityObj || !g_updateProgressMid) return;

    // We need to attach the current thread to the JVM to perform the callback
    // (Otr generation runs on a background thread in your Java code)
    // Note: In a production environment, use a cached JavaVM* to get the correct Env.
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, 
                                                jint romFd, 
                                                jobject assetManager, 
                                                jstring outputDir) {
    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    // 1. Load manifest.bin from APK assets
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        
        // 2. Pass JNIEnv and GlobalRef to the builder so it can call updateOtrProgress
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              romFd, manifestBuffer, outDir);
        
        AAsset_close(asset);
    }

    env->ReleaseStringUTFChars(outputDir, outDir);
}
