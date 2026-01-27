#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include "otr_builder.h"

extern "C"
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_runOtrGeneration(JNIEnv* env, jclass clazz, 
                                                jint romFd, 
                                                jobject assetManager, 
                                                jstring outputDir) {
    
    const char* oDir = env->GetStringUTFChars(outputDir, nullptr);
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    
    // Using manifest_us.bin as a default
    AAsset* asset = AAssetManager_open(mgr, "manifest_us.bin", AASSET_MODE_BUFFER);
    
    if (!asset) {
        env->ReleaseStringUTFChars(outputDir, oDir);
        return JNI_FALSE;
    }

    uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);

    // We need the method ID here if we aren't using the cached one from nativeInit
    // For simplicity, let's assume nativeInit was called, or pass nulls
    run_native_otr_generation_with_callback(env, nullptr, nullptr, romFd, manifestBuffer, oDir);

    AAsset_close(asset);
    env->ReleaseStringUTFChars(outputDir, oDir);

    return JNI_TRUE;
}
