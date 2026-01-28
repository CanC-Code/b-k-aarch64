#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <cstring>
#include <string>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

// Global references for JNI callbacks
static jobject g_callbackObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;

extern "C" {
    // libultra scheduler state (from your exceptasm.cpp)
    extern void initInterruptTables();
    extern void __osDispatchThread();
    
    // Decompilation entry points
    extern void boot(); 
    extern void Engine_RunFrame(); 
    
    // Engine asset management (The bridge between OTR and the Game)
    // Adjust these names based on your specific decomp's resource loader
    extern void ResourceMgr_Init(const char* otrPath);
}

extern "C" {

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    otr_builder_set_jvm(vm); 
    return JNI_VERSION_1_6;
}

/**
 * PROGRESS CALLBACK SETUP
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject callbackTarget) {
    if (g_callbackObj != nullptr) {
        env->DeleteGlobalRef(g_callbackObj);
    }
    g_callbackObj = env->NewGlobalRef(callbackTarget);

    jclass serviceClass = env->GetObjectClass(g_callbackObj);
    g_updateProgressMid = env->GetMethodID(serviceClass, "updateOtrProgress", "(ILjava/lang/String;)V");
}

/**
 * ASSET EXTRACTION (OTR GENERATION)
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz,
                                                jint romFd, jobject assetManager, jstring outputDir) {
    if (g_callbackObj == nullptr) return;

    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    // Ensure this matches your manifest filename in assets/
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

/**
 * ENGINE STARTUP
 * @param otrPath: The internal storage path where the .otr file was generated.
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeGameBoot(JNIEnv* env, jclass clazz, jstring otrPath) {
    const char* cOtrPath = env->GetStringUTFChars(otrPath, nullptr);
    
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Initializing Resource Manager with: %s", cOtrPath);
    
    // 1. Tell the engine where the extracted assets are
    // ResourceMgr_Init(cOtrPath); 
    
    // 2. Setup libultra scheduler
    initInterruptTables();
    
    // 3. Start N64 logic
    boot();
    
    env->ReleaseStringUTFChars(otrPath, cOtrPath);
}

/**
 * TICK / FRAME LOOP
 * Called by Android's Choreographer (linked to screen refresh rate)
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeMainLoop(JNIEnv* env, jclass clazz) {
    // Execute one step of the game logic
    Engine_RunFrame();

    // Force a scheduler check to process N64 thread messages
    __osDispatchThread();
}

} // extern "C"
