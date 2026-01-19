#include <jni.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <vector>
#include <string>
#include "otr_generator.hpp"

#define LOG_TAG "BKA_NativeBridge"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

static OTRGenerator g_otrGenerator;

// JNI bridge

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass, jobject assetManager) {
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    g_otrGenerator.initAssetManager(mgr);
    LOGI("NativeBridge initialized");
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_nativeGenerateOTR(
        JNIEnv* env, jclass, jbyteArray romData, jstring yamlAssetPath) {

    const char* yamlPath = env->GetStringUTFChars(yamlAssetPath, nullptr);

    jsize romSize = env->GetArrayLength(romData);
    std::vector<uint8_t> romBuffer(romSize);
    env->GetByteArrayRegion(romData, 0, romSize, reinterpret_cast<jbyte*>(romBuffer.data()));

    bool success = g_otrGenerator.generateOTRFromROM(romBuffer, yamlPath);

    env->ReleaseStringUTFChars(yamlAssetPath, yamlPath);
    return success ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_nativeGetProgress(JNIEnv*, jclass) {
    return g_otrGenerator.getProgress();
}

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeLoadOTR(JNIEnv*, jclass) {
    g_otrGenerator.loadGeneratedOTRIntoRenderer();
}