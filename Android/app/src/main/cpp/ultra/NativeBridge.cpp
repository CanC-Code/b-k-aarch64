#include <sched.h>
#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <cstring>
#include <string>

#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

static jobject g_callbackObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;

extern "C" {
    extern void initInterruptTables();
    extern void __osDispatchThread();
    extern void boot(); 
    extern void Engine_RunFrame(); 
    extern void ResourceMgr_Init(const char* otrPath, uint8_t* manifestBuf, uint32_t manifestSize);
}

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
    g_callbackObj = env->NewGlobalRef(callbackTarget);
    jclass serviceClass = env->GetObjectClass(g_callbackObj);
    g_updateProgressMid = env->GetMethodID(serviceClass, "updateOtrProgress", "(ILjava/lang/String;)V");
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
    } else {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Failed to open manifest_us.bin!");
    }
    env->ReleaseStringUTFChars(outputDir, outDir);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeGameBoot(JNIEnv* env, jclass clazz, jstring otrPath, jobject assetManager) {
    const char* cOtrPath = env->GetStringUTFChars(otrPath, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    AAsset* manifestAsset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (manifestAsset) {
        uint8_t* buf = (uint8_t*)AAsset_getBuffer(manifestAsset);
        uint32_t size = (uint32_t)AAsset_getLength(manifestAsset);

        ResourceMgr_Init(cOtrPath, buf, size);
        AAsset_close(manifestAsset);
    }

    initInterruptTables();
    boot();

    // MUST release the string chars after the engine starts
    env->ReleaseStringUTFChars(otrPath, cOtrPath);
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeMainLoop(JNIEnv* env, jclass clazz) {
    Engine_RunFrame();
    __osDispatchThread();
    
    // Hint to the OS to yield if we're ahead of frame time
    ::sched_yield(); 
}

} // extern "C"
