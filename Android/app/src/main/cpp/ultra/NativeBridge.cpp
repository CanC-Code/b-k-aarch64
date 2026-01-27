#include <jni.h>
#include <unistd.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

// Globals to store JNI state
static jobject g_mainActivityObj = nullptr;
static jmethodID g_updateProgressMid = nullptr;
static JavaVM* g_jvm = nullptr;

extern "C" {

// 1. Initialize the bridge and capture the JVM
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject activity) {
    // Capture the VM so background threads can attach to it later
    env->GetJavaVM(&g_jvm);
    
    // Pass the VM to your builder if it needs it internally
    otr_builder_set_jvm(g_jvm); 
    
    // Create a Global Reference so the activity isn't GC'd during extraction
    if (g_mainActivityObj != nullptr) {
        env->DeleteGlobalRef(g_mainActivityObj);
    }
    g_mainActivityObj = env->NewGlobalRef(activity);
    
    // Match the method name exactly: updateOtrProgress
    jclass activityClass = env->GetObjectClass(activity);
    g_updateProgressMid = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");
    
    if (g_updateProgressMid == nullptr) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "CRITICAL: updateOtrProgress method not found!");
    }
}

// 2. Run generation with FD protection
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, 
                                                jint romFd, 
                                                jobject assetManager, 
                                                jstring outputDir) {
    
    // CRITICAL: Duplicate the FD. This allows the native code to keep 
    // the file open even if Java closes the original Uri descriptor.
    int nativeFd = dup(romFd); 
    if (nativeFd == -1) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Failed to duplicate ROM FD");
        return;
    }

    const char* outDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);

    // Load the manifest from assets
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    if (asset) {
        uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
        
        // Pass the duplicated FD (nativeFd) instead of the raw romFd
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              nativeFd, manifestBuffer, outDir);
        AAsset_close(asset);
    }

    // Cleanup
    close(nativeFd); 
    env->ReleaseStringUTFChars(outputDir, outDir);
}

// ... Keep other stubs (startGameLoop, etc.) as they were ...
}
