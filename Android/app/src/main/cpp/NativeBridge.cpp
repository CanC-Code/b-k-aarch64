#include <jni.h>
#include <android/asset_manager_jni.h>
#include <android/asset_manager.h>
#include <vector>
#include <string>
#include <mutex>

#include "OTRGenerator.hpp"

// Single in-memory buffer for generated OTR
static std::vector<uint8_t> gOTRBuffer;
static std::mutex gOTRMutex;

static AAssetManager* gAssetManager = nullptr;

// ---- JNI EXPORTS ----

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass, jobject assetManager) {
    gAssetManager = AAssetManager_fromJava(env, assetManager);
}

// Load YAML asset into memory
static std::vector<uint8_t> loadYAMLAsset(const char* assetPath) {
    std::vector<uint8_t> data;

    if (!gAssetManager) return data;

    AAsset* asset = AAssetManager_open(gAssetManager, assetPath, AASSET_MODE_BUFFER);
    if (!asset) return data;

    size_t size = AAsset_getLength(asset);
    data.resize(size);
    AAsset_read(asset, data.data(), size);
    AAsset_close(asset);

    return data;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_nativeGenerateOTR(
        JNIEnv* env,
        jclass,
        jbyteArray romData,
        jstring yamlAssetPath,
        jstring outputDir) {

    if (!romData || !yamlAssetPath) return JNI_FALSE;

    const char* yamlPath = env->GetStringUTFChars(yamlAssetPath, nullptr);

    // Load YAML from APK assets
    std::vector<uint8_t> yamlData = loadYAMLAsset(yamlPath);
    env->ReleaseStringUTFChars(yamlAssetPath, yamlPath);

    if (yamlData.empty()) return JNI_FALSE;

    // Load ROM bytes from JVM array
    jsize romSize = env->GetArrayLength(romData);
    std::vector<uint8_t> romBytes(romSize);
    env->GetByteArrayRegion(romData, 0, romSize, reinterpret_cast<jbyte*>(romBytes.data()));

    // Generate OTR into gOTRBuffer
    {
        std::lock_guard<std::mutex> lock(gOTRMutex);
        gOTRBuffer.clear();
        bool ok = OTRGenerator::generateOTR(romBytes.data(), romBytes.size(),
                                             yamlData.data(), yamlData.size(),
                                             gOTRBuffer);
        return ok ? JNI_TRUE : JNI_FALSE;
    }
}

extern "C" JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_nativeGetProgress(JNIEnv*, jclass) {
    return OTRGenerator::getProgress(); // returns 0.0f–1.0f
}

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeLoadOTR(JNIEnv*, jclass, jstring) {
    // No disk path needed; GLRenderer reads gOTRBuffer directly
}
    
// Provide access to in-memory OTR for GLRenderer
const uint8_t* getGeneratedOTR(size_t& outSize) {
    std::lock_guard<std::mutex> lock(gOTRMutex);
    outSize = gOTRBuffer.size();
    return gOTRBuffer.data();
}