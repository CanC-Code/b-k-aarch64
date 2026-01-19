#include <jni.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <vector>
#include <string>
#include <mutex>

#include "OTRGenerator.hpp"

#define LOG_TAG "NativeBridge"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

static AAssetManager* g_assetManager = nullptr;
static std::vector<uint8_t> g_generatedOTR;
static std::mutex g_mutex;

// Forward declaration
float getProgressCallback();

// -------------------------------
// JNI: Initialize native system
// -------------------------------
extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass, jobject assetManager) {
    g_assetManager = AAssetManager_fromJava(env, assetManager);
    if (!g_assetManager) {
        LOGE("Failed to get native AssetManager");
    } else {
        LOGI("AssetManager initialized");
    }
}

// -------------------------------
// JNI: Generate OTR dynamically
// -------------------------------
extern "C" JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_nativeGenerateOTR(
        JNIEnv* env,
        jclass,
        jbyteArray romData,
        jstring yamlAssetPath,
        jstring outputDir
) {
    if (!g_assetManager) {
        LOGE("AssetManager not initialized");
        return JNI_FALSE;
    }

    const char* yamlPathC = env->GetStringUTFChars(yamlAssetPath, nullptr);
    std::string yamlPath(yamlPathC);
    env->ReleaseStringUTFChars(yamlAssetPath, yamlPathC);

    // Convert ROM bytes
    jsize romSize = env->GetArrayLength(romData);
    std::vector<uint8_t> romBuffer(romSize);
    env->GetByteArrayRegion(romData, 0, romSize, reinterpret_cast<jbyte*>(romBuffer.data()));

    // Load YAML from assets
    AAsset* asset = AAssetManager_open(g_assetManager, yamlPath.c_str(), AASSET_MODE_BUFFER);
    if (!asset) {
        LOGE("Failed to open YAML asset: %s", yamlPath.c_str());
        return JNI_FALSE;
    }
    size_t yamlSize = static_cast<size_t>(AAsset_getLength(asset));
    std::vector<uint8_t> yamlBuffer(yamlSize);
    AAsset_read(asset, yamlBuffer.data(), yamlSize);
    AAsset_close(asset);

    // Lock OTR buffer
    std::lock_guard<std::mutex> lock(g_mutex);
    g_generatedOTR.clear();

    // Generate OTR in memory
    bool result = OTRGenerator::generateOTR(
            romBuffer,
            yamlBuffer,
            g_generatedOTR,
            getProgressCallback
    );

    return result ? JNI_TRUE : JNI_FALSE;
}

// -------------------------------
// JNI: Return progress [0.0 - 1.0]
// -------------------------------
extern "C" JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_nativeGetProgress(JNIEnv*, jclass) {
    return getProgressCallback();
}

// -------------------------------
// JNI: Load OTR into renderer
// -------------------------------
extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeLoadOTR(
        JNIEnv*,
        jclass,
        jstring /* otrPath not needed, using memory buffer */
) {
    // No-op: renderer will consume g_generatedOTR directly
}

// -------------------------------
// Retrieve generated OTR bytes for GLRenderer
// -------------------------------
extern "C"
JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getGeneratedOTRBytes(JNIEnv* env, jclass) {
    std::lock_guard<std::mutex> lock(g_mutex);
    jbyteArray arr = env->NewByteArray(static_cast<jsize>(g_generatedOTR.size()));
    if (!arr) return nullptr;
    env->SetByteArrayRegion(arr, 0, static_cast<jsize>(g_generatedOTR.size()),
                            reinterpret_cast<const jbyte*>(g_generatedOTR.data()));
    return arr;
}

// -------------------------------
// Dummy progress callback (can be extended for real progress)
// -------------------------------
static float g_progress = 0.0f;
float getProgressCallback() {
    return g_progress; // For now always 1.0 when done
}