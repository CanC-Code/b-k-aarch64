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
    // libultra scheduler state (from exceptasm.cpp)
    extern void initInterruptTables();
    extern void __osDispatchThread();
    
    // Decompilation entry points
    extern void boot(); 
    extern void Engine_RunFrame(); 
    
    // Updated Resource Manager Init (from emulator/resource_mgr.cpp)
    extern void ResourceMgr_Init(const char* otrPath, uint8_t* manifestBuf, uint32_t manifestSize);
}

extern "C" {

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    otr_builder_set_jvm(vm); 
    return JNI_VERSION_1_6;
}

/**
 * PROGRESS CALLBACK SETUP
 * Initializes communication back to the Java UI for the OTR builder.
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
 * Extracts the ROM data into an OTR file.
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz,
                                                jint romFd, jobject assetManager, jstring outputDir) {
    if (g_callbackObj == nullptr) return;

    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    // Load manifest from assets to guide the extraction
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);

    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        uint32_t manifestSize = (uint32_t)AAsset_getLength(asset);

        run_native_otr_generation_with_callback(env, g_callbackObj, g_updateProgressMid,
                                              romFd, manifestBuffer, manifestSize, outDir);
        AAsset_close(asset);
    } else {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Failed to open manifest_us.bin for extraction!");
    }
    env->ReleaseStringUTFChars(outputDir, outDir);
}

/**
 * ENGINE STARTUP
 * @param otrPath: The internal storage path where the .otr file was generated.
 * @param assetManager: The Android AssetManager to load the manifest.
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeGameBoot(JNIEnv* env, jclass clazz, jstring otrPath, jobject assetManager) {
    const char* cOtrPath = env->GetStringUTFChars(otrPath, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Booting Engine. OTR Path: %s", cOtrPath);
    
    // 1. Load the manifest and initialize the Resource Manager
    // This allows DMA requests to find assets within the OTR file.
    AAsset* manifestAsset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (manifestAsset) {
        uint8_t* buf = (uint8_t*)AAsset_getBuffer(manifestAsset);
        uint32_t size = (uint32_t)AAsset_getLength(manifestAsset);
        
        ResourceMgr_Init(cOtrPath, buf, size);
        
        // Note: We don't close the asset immediately if the ResourceMgr 
        // points directly to the buffer. If ResourceMgr copies the data, close it.
        AAsset_close(manifestAsset);
    } else {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "CRITICAL: Could not load manifest for ResourceMgr!");
    }
    
    // 2. Setup libultra scheduler (Interrupts)
    initInterruptTables();
    
    // 3. Start N64 logic (Idle Thread / Main entry)
    boot();
    
    env->ReleaseStringUTFChars(otrPath, cOtrPath);
}

/**
 * TICK / FRAME LOOP
 * Called by Android's Choreographer (linked to screen refresh rate).
 */
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeMainLoop(JNIEnv* env, jclass clazz) {
    // Execute one step of the decompiled game logic
    Engine_RunFrame();

    // Trigger the virtual interrupt/scheduler to process thread messages
    __osDispatchThread();
}

} // extern "C"
