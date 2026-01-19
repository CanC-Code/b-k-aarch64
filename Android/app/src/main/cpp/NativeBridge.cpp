#include <jni.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <vector>
#include <string>

#include "otr_generator.hpp"

#define LOG_TAG "BKA"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

static AAssetManager* g_assetManager = nullptr;
static float g_progress = 0.0f;

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(
        JNIEnv* env,
        jclass,
        jobject assetManager) {

    g_assetManager = AAssetManager_fromJava(env, assetManager);
    LOGI("AssetManager initialized");
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_nativeGenerateOTR(
        JNIEnv* env,
        jclass,
        jbyteArray romData,
        jstring yamlAssetPath,
        jstring outputDir) {

    if (!g_assetManager) {
        LOGE("AssetManager not initialized");
        return JNI_FALSE;
    }

    const jsize romSize = env->GetArrayLength(romData);
    std::vector<uint8_t> romBuffer(romSize);
    env->GetByteArrayRegion(romData, 0, romSize,
                            reinterpret_cast<jbyte*>(romBuffer.data()));

    const char* yamlPath = env->GetStringUTFChars(yamlAssetPath, nullptr);
    const char* outDir   = env->GetStringUTFChars(outputDir, nullptr);

    bool success = GenerateOTR(
            romBuffer.data(),
            romBuffer.size(),
            g_assetManager,
            yamlPath,
            outDir,
            [](float p) { g_progress = p; }
    );

    env->ReleaseStringUTFChars(yamlAssetPath, yamlPath);
    env->ReleaseStringUTFChars(outputDir, outDir);

    return success ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_nativeGetProgress(
        JNIEnv*, jclass) {
    return g_progress;
}

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeLoadOTR(
        JNIEnv* env,
        jclass,
        jstring otrPath) {

    const char* path = env->GetStringUTFChars(otrPath, nullptr);
    // Hook into renderer / OTR loader here
    LOGI("Loading OTR from %s", path);
    env->ReleaseStringUTFChars(otrPath, path);
}