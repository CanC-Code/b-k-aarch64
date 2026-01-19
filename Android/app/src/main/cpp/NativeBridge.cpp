#include <jni.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <vector>
#include <string>
#include <mutex>
#include <cstring>

#define LOG_TAG "NativeBridge"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ------------------------------
// Global state
// ------------------------------
static std::vector<uint8_t> gOTRData;          // Holds dynamically generated OTR array
static std::mutex gOTRMutex;                   // Protect concurrent access
static float gProgress = 0.0f;

// ------------------------------
// Forward declarations
// ------------------------------
extern "C" {
    JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject assetManager);
    JNIEXPORT jboolean JNICALL Java_com_bkawrapper_NativeBridge_nativeGenerateOTR(JNIEnv* env, jclass clazz, jbyteArray romData, jstring yamlPath, jstring outputDir);
    JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_nativeLoadOTR(JNIEnv* env, jclass clazz, jstring otrPath);
    JNIEXPORT jfloat JNICALL Java_com_bkawrapper_NativeBridge_nativeGetProgress(JNIEnv* env, jclass clazz);
    JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_nativeRender(JNIEnv* env, jclass clazz);
}

// ------------------------------
// Initialize native renderer
// ------------------------------
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_nativeInit(JNIEnv* env, jclass clazz, jobject assetManager) {
    LOGI("Native renderer initialized.");
    // TODO: Initialize OpenGL, framebuffers, etc.
}

// ------------------------------
// Generate OTR from ROM + YAML
// ------------------------------
JNIEXPORT jboolean JNICALL Java_com_bkawrapper_NativeBridge_nativeGenerateOTR(
        JNIEnv* env, jclass clazz,
        jbyteArray romData,
        jstring yamlPath,
        jstring outputDir) {

    std::lock_guard<std::mutex> lock(gOTRMutex);

    // Reset progress
    gProgress = 0.0f;

    // Extract ROM bytes
    jsize romSize = env->GetArrayLength(romData);
    std::vector<uint8_t> romBuffer(romSize);
    env->GetByteArrayRegion(romData, 0, romSize, reinterpret_cast<jbyte*>(romBuffer.data()));

    // Extract YAML path
    const char* yamlCStr = env->GetStringUTFChars(yamlPath, nullptr);
    std::string yamlAsset(yamlCStr);
    env->ReleaseStringUTFChars(yamlPath, yamlCStr);

    // Extract output directory
    const char* outputCStr = env->GetStringUTFChars(outputDir, nullptr);
    std::string outDir(outputCStr);
    env->ReleaseStringUTFChars(outputDir, outputCStr);

    LOGI("Generating OTR from ROM (%zu bytes) with YAML: %s", romBuffer.size(), yamlAsset.c_str());

    // Simulate YAML + ROM processing to create .inc array
    gOTRData.clear();
    gOTRData.reserve(romBuffer.size() + 1024); // reserve extra space
    for (size_t i = 0; i < romBuffer.size(); ++i) {
        gOTRData.push_back(romBuffer[i] ^ 0xAA); // simple XOR as placeholder
        if (i % (romBuffer.size() / 10 + 1) == 0) {
            gProgress = float(i) / float(romBuffer.size());
        }
    }
    gProgress = 1.0f;

    // Write to internal storage as latest.otr
    std::string outPath = outDir + "/latest.otr";
    FILE* f = fopen(outPath.c_str(), "wb");
    if (!f) {
        LOGE("Failed to open output OTR file: %s", outPath.c_str());
        return JNI_FALSE;
    }
    fwrite(gOTRData.data(), 1, gOTRData.size(), f);
    fclose(f);

    LOGI("OTR generation complete: %zu bytes -> %s", gOTRData.size(), outPath.c_str());
    return JNI_TRUE;
}

// ------------------------------
// Load OTR into memory for renderer
// ------------------------------
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_nativeLoadOTR(
        JNIEnv* env, jclass clazz, jstring otrPath) {

    const char* pathCStr = env->GetStringUTFChars(otrPath, nullptr);
    std::string path(pathCStr);
    env->ReleaseStringUTFChars(otrPath, pathCStr);

    FILE* f = fopen(path.c_str(), "rb");
    if (!f) {
        LOGE("Failed to open OTR file for loading: %s", path.c_str());
        return;
    }

    std::lock_guard<std::mutex> lock(gOTRMutex);
    gOTRData.clear();
    fseek(f, 0, SEEK_END);
    size_t size = ftell(f);
    fseek(f, 0, SEEK_SET);
    gOTRData.resize(size);
    fread(gOTRData.data(), 1, size, f);
    fclose(f);

    LOGI("Loaded OTR into memory: %zu bytes", gOTRData.size());
}

// ------------------------------
// Get progress [0.0 – 1.0]
// ------------------------------
JNIEXPORT jfloat JNICALL Java_com_bkawrapper_NativeBridge_nativeGetProgress(JNIEnv* env, jclass clazz) {
    std::lock_guard<std::mutex> lock(gOTRMutex);
    return gProgress;
}

// ------------------------------
// Render frame using in-memory OTR
// ------------------------------
JNIEXPORT void JNICALL Java_com_bkawrapper_NativeBridge_nativeRender(JNIEnv* env, jclass clazz) {
    std::lock_guard<std::mutex> lock(gOTRMutex);
    if (gOTRData.empty()) return;

    // TODO: Replace with real OpenGL rendering of OTR
    // Placeholder: just clear screen with a color based on first byte
    uint8_t color = gOTRData[0];
    glClearColor(color / 255.0f, 0.2f, 0.3f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);
}