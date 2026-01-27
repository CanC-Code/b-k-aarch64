#include <jni.h>
#include <unistd.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

// Globals for JNI callbacks
static jobject g_mainActivityObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;
static JavaVM* g_jvm = nullptr;

extern "C" {

// 1. Initialize the bridge and store references
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject activity) {
    env->GetJavaVM(&g_jvm);
    
    // Create a global reference to the activity so it's not GC'd
    if (g_mainActivityObj != nullptr) {
        env->DeleteGlobalRef(g_mainActivityObj);
    }
    g_mainActivityObj = env->NewGlobalRef(activity);
    
    // Find the Java class and the method ID
    // Note: Changed "onOtrProgress" to "updateOtrProgress" to match your MainActivity
    jclass activityClass = env->GetObjectClass(activity);
    g_updateProgressMid = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");
    
    if (g_updateProgressMid == nullptr) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Failed to find updateOtrProgress method!");
    }
}

// 2. Run OTR Generation with File Descriptor protection
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, 
                                                jint romFd, 
                                                jobject assetManager, 
                                                jstring outputDir) {
    
    // DUPLICATE THE FD: This ensures native background threads can read the ROM
    // even if Java closes the original descriptor.
    int nativeFd = dup(romFd); 
    if (nativeFd == -1) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Failed to duplicate FD");
        return;
    }

    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    // Open the manifest file from the APK assets
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        
        // Call the internal generation logic
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              nativeFd, manifestBuffer, outDir);
        AAsset_close(asset);
    }

    // CLEANUP
    close(nativeFd); 
    env->ReleaseStringUTFChars(outputDir, outDir);
}

// 3. Texture Stubs (To match your updated NativeBridge.java)
JNIEXPORT jint JNICALL
Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv* env, jclass clazz) {
    // Return a default texture ID or implementation
    return 0;
}

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv* env, jclass clazz, jint tid) {
    // Texture update logic here
}

// 4. Game Loop Stubs
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv* env, jclass clazz) { /* ... */ }
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_pauseGameLoop(JNIEnv* env, jclass clazz) { /* ... */ }
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_resumeGameLoop(JNIEnv* env, jclass clazz) { /* ... */ }
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv* env, jclass clazz) { /* ... */ }

} // extern "C"
