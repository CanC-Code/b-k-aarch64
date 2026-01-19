#include <jni.h>
#include <vector>
#include <string>
#include <mutex>
#include <android/asset_manager_jni.h>
#include <android/log.h>

#define LOG_TAG "OTRGenerator"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Thread-safe storage for the generated OTR
static std::vector<uint8_t> gOTRData;
static std::mutex gOTRMutex;
static float gProgress = 0.0f;

// Simple YAML loader from AssetManager
static std::string loadAsset(AAssetManager* mgr, const char* assetPath) {
    AAsset* asset = AAssetManager_open(mgr, assetPath, AASSET_MODE_BUFFER);
    if (!asset) {
        LOGE("Failed to open asset: %s", assetPath);
        return "";
    }
    size_t size = AAsset_getLength(asset);
    std::string data(size, '\0');
    int readBytes = AAsset_read(asset, data.data(), size);
    AAsset_close(asset);

    if (readBytes != (int)size) {
        LOGE("Asset read mismatch: %s", assetPath);
        return "";
    }
    return data;
}

// Mock OTR generation: combine ROM + YAML
static void generateOTRInternal(const uint8_t* romData, size_t romSize, const std::string& yaml, std::vector<uint8_t>& out) {
    out.clear();
    out.reserve(romSize + yaml.size());

    for (size_t i = 0; i < romSize; i++) {
        out.push_back(romData[i]);
        gProgress = i / (float)romSize * 0.5f;
    }
    for (size_t i = 0; i < yaml.size(); i++) {
        out.push_back(yaml[i]);
        gProgress = 0.5f + (i / (float)yaml.size()) * 0.5f;
    }
    gProgress = 1.0f;
}

// JNI interface
extern "C" {

// Initialize generator (not much to do here)
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitOTR(JNIEnv* env, jclass clazz) {
    std::lock_guard<std::mutex> lock(gOTRMutex);
    gOTRData.clear();
    gProgress = 0.0f;
}

// Generate OTR from ROM + YAML asset path
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_nativeGenerateOTR(
        JNIEnv* env,
        jclass clazz,
        jbyteArray romArray,
        jobject assetManager,
        jstring yamlPath) {

    if (!romArray || !assetManager || !yamlPath) return JNI_FALSE;

    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    if (!mgr) return JNI_FALSE;

    jsize romSize = env->GetArrayLength(romArray);
    std::vector<uint8_t> romData(romSize);
    env->GetByteArrayRegion(romArray, 0, romSize, reinterpret_cast<jbyte*>(romData.data()));

    const char* yamlCStr = env->GetStringUTFChars(yamlPath, nullptr);
    std::string yamlData = loadAsset(mgr, yamlCStr);
    env->ReleaseStringUTFChars(yamlPath, yamlCStr);

    if (yamlData.empty()) return JNI_FALSE;

    {
        std::lock_guard<std::mutex> lock(gOTRMutex);
        generateOTRInternal(romData.data(), romSize, yamlData, gOTRData);
    }

    LOGI("OTR generation completed, size: %zu bytes", gOTRData.size());
    return JNI_TRUE;
}

// Get progress [0.0 – 1.0]
JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_nativeGetProgress(JNIEnv* env, jclass clazz) {
    std::lock_guard<std::mutex> lock(gOTRMutex);
    return gProgress;
}

// Load OTR for renderer (return pointer to data)
JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_nativeLoadOTR(JNIEnv* env, jclass clazz) {
    std::lock_guard<std::mutex> lock(gOTRMutex);
    jbyteArray arr = env->NewByteArray(gOTRData.size());
    env->SetByteArrayRegion(arr, 0, gOTRData.size(), reinterpret_cast<const jbyte*>(gOTRData.data()));
    return arr;
}

} // extern "C"