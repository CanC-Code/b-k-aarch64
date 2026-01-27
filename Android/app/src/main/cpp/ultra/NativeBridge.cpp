#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

#define LOG_TAG "NativeBridge"

// Use extern variables defined in wrapper.cpp instead of redefining them
extern jobject g_mainActivityObj;
extern jmethodID g_updateProgressMid;

extern "C" {

// REMOVED: Java_com_bkawrapper_NativeBridge_nativeInit 
// (Keep the definition in wrapper.cpp instead)

JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, 
                                                jint romFd, jobject assetManager, jstring outputDir) {
    [span_3](start_span)const char* outDir = env->GetStringUTFChars(outputDir, nullptr);[span_3](end_span)
    [span_4](start_span)AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);[span_4](end_span)

    [span_5](start_span)AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);[span_5](end_span)
    if (asset) {
        [span_6](start_span)uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);[span_6](end_span)
        
        // Call the orchestrator
        run_native_otr_generation_with_callback(env, g_mainActivityObj, g_updateProgressMid, 
                                              [span_7](start_span)romFd, manifestBuffer, outDir);[span_7](end_span)
        [span_8](start_span)AAsset_close(asset);[span_8](end_span)
    } else {
        _[span_9](start_span)_android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Could not find manifest_us.bin");[span_9](end_span)
    }
    [span_10](start_span)env->ReleaseStringUTFChars(outputDir, outDir);[span_10](end_span)
}

// REMOVED: Game Loop and Texture Stubs
// (These should stay in wrapper.cpp to avoid duplication)

} // extern "C"
