#include <jni.h>      // <--- ADD THIS LINE (Fixes build error)
#include <unistd.h>   // Required for dup() and close()
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

// ... (keep existing global variables)

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, 
                                                jint romFd, 
                                                jobject assetManager, 
                                                jstring outputDir) {
    // DUPLICATE THE FD (Prevents the "crash after selecting ROM")
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
        // Use the duplicated nativeFd here
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              nativeFd, manifestBuffer, outDir);
        AAsset_close(asset);
    }

    // Clean up
    close(nativeFd); 
    env->ReleaseStringUTFChars(outputDir, outDir);
}
