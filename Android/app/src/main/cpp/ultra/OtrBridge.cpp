// Android/app/src/main/cpp/ultra/OtrBridge.cpp
#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include "otr_builder.h"

extern "C"
JNIEXPORT jboolean JNICALL
Java_com_yourproject_app_OtrBridge_runExtraction(JNIEnv* env, jobject thiz, 
                                                jint romFd, 
                                                jobject assetManager, 
                                                jstring manifestPath, 
                                                jstring outputDir) {
    
    // 1. Convert Java Strings to C Strings
    const char* mPath = env->GetStringUTFChars(manifestPath, nullptr);
    const char* oDir = env->GetStringUTFChars(outputDir, nullptr);

    // 2. Load the Binary Manifest from APK Assets
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    AAsset* asset = AAssetManager_open(mgr, mPath, AASSET_MODE_BUFFER);
    
    if (!asset) {
        env->ReleaseStringUTFChars(manifestPath, mPath);
        env->ReleaseStringUTFChars(outputDir, oDir);
        return JNI_FALSE;
    }

    uint8_t* manifestBuffer = (uint8_t*)AAsset_getBuffer(asset);
    size_t manifestSize = AAsset_getLength(asset);

    // 3. Call your native OTR generator
    // (Ensure run_otr_generation is declared in otr_builder.h)
    run_otr_generation(romFd, manifestBuffer, oDir);

    // 4. Cleanup
    AAsset_close(asset);
    env->ReleaseStringUTFChars(manifestPath, mPath);
    env->ReleaseStringUTFChars(outputDir, oDir);

    return JNI_TRUE;
}
