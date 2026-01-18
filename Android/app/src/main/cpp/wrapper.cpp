// File: Android/app/src/main/cpp/wrapper.cpp
#include <jni.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <vector>
#include <mutex>
#include "otr_generator.h"

#define LOG_TAG "WrapperCPP"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// -------------------------------
// Progress tracking
// -------------------------------
static std::mutex progressMutex;
static float currentProgress = 0.0f;

// Internal function for OTR progress updates
void updateProgress(float progress) {
    std::lock_guard<std::mutex> lock(progressMutex);
    currentProgress = progress;
}

// -------------------------------
// JNI: process ROM & generate OTR
// -------------------------------
extern "C"
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_nativeProcessRom(
        JNIEnv* env,
        jclass clazz,
        jbyteArray romData,
        jint romSize
) {
    if (!romData || romSize <= 0) return JNI_FALSE;

    jbyte* romBytes = env->GetByteArrayElements(romData, nullptr);
    std::vector<uint8_t> romVec(romBytes, romBytes + romSize);
    env->ReleaseByteArrayElements(romData, romBytes, 0);

    std::vector<uint8_t> outOTR;

    // Reset progress
    updateProgress(0.0f);

    // Build OTR using embedded YAML
    bool success = buildOTRForROM(nullptr, romVec.data(), romVec.size(), outOTR);

    // OTR generation finished → mark progress complete
    updateProgress(1.0f);

    LOGI("nativeProcessRom finished, size=%zu, success=%d", outOTR.size(), success);

    return success ? JNI_TRUE : JNI_FALSE;
}

// -------------------------------
// JNI: get current OTR progress
// -------------------------------
extern "C"
JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_nativeGetOTRProgress(
        JNIEnv* env,
        jclass clazz
) {
    std::lock_guard<std::mutex> lock(progressMutex);
    return currentProgress;
}

// -------------------------------
// Game/OpenGL stubs
// -------------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitGame(
        JNIEnv* env,
        jclass clazz,
        jobject surface
) {
    LOGI("nativeInitGame called");
    // TODO: attach to your OpenGL engine
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeInitTexture(
        JNIEnv* env,
        jclass clazz
) {
    LOGI("nativeInitTexture called");
    // TODO: setup texture in your OpenGL context
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeStartGameLoop(
        JNIEnv* env,
        jclass clazz
) {
    LOGI("nativeStartGameLoop called");
    // TODO: start game loop thread
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeStopGameLoop(
        JNIEnv* env,
        jclass clazz
) {
    LOGI("nativeStopGameLoop called");
    // TODO: stop game loop thread
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeCleanupGame(
        JNIEnv* env,
        jclass clazz
) {
    LOGI("nativeCleanupGame called");
    // TODO: cleanup resources
}