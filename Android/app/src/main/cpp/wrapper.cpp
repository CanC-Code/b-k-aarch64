// File: Android/app/src/main/cpp/wrapper.cpp
#include <jni.h>
#include <vector>
#include <cstdint>
#include <cstring>
#include <android/log.h>
#include <android/asset_manager_jni.h>

#include "ultra/otr_builder.h" // Your OTR builder with progress support

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ---------------- Global state ----------------
static std::vector<uint8_t> g_rom;
static std::vector<uint8_t> g_otr;

// Progress tracking
static float g_otrProgress = 0.0f;

extern "C"
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_processRom(
        JNIEnv* env,
        jclass,
        jbyteArray romData)
{
    if (!romData) {
        LOGE("ROM data is null");
        return JNI_FALSE;
    }

    const jsize romSize = env->GetArrayLength(romData);
    if (romSize <= 0) {
        LOGE("ROM size invalid");
        return JNI_FALSE;
    }

    g_rom.resize(static_cast<size_t>(romSize));
    env->GetByteArrayRegion(
        romData,
        0,
        romSize,
        reinterpret_cast<jbyte*>(g_rom.data())
    );

    LOGI("ROM received: %d bytes", romSize);

    g_otr.clear();
    g_otrProgress = 0.0f;

    // Example OTR builder with progress callback
    auto progressCallback = [](float progress) {
        g_otrProgress = progress; // store progress for JNI polling
    };

    const bool success = buildBKOTR(
        g_rom.data(),
        g_rom.size(),
        nullptr,  // yamlData optional if using embedded bin
        0,
        g_otr,
        progressCallback
    );

    if (!success || g_otr.empty()) {
        LOGE("OTR build failed");
        g_otrProgress = 0.0f;
        return JNI_FALSE;
    }

    g_otrProgress = 1.0f;
    LOGI("OTR build complete: %zu bytes", g_otr.size());
    return JNI_TRUE;
}

extern "C"
JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getOTR(
        JNIEnv* env,
        jclass)
{
    if (g_otr.empty()) {
        LOGE("OTR buffer empty");
        return nullptr;
    }

    jbyteArray out = env->NewByteArray(static_cast<jsize>(g_otr.size()));
    env->SetByteArrayRegion(out, 0, static_cast<jsize>(g_otr.size()),
                            reinterpret_cast<const jbyte*>(g_otr.data()));
    return out;
}

extern "C"
JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getOTRProgress(
        JNIEnv* env,
        jclass)
{
    return g_otrProgress;
}

// ---------------- Game / OpenGL stubs ----------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initGame(JNIEnv* env, jclass, jobject surface) {
    // Initialize your GL context / game engine
    LOGI("Game initialized");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv* env, jclass) {
    LOGI("Game cleanup");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv* env, jclass) {
    LOGI("Game loop started");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_stopGameLoop(JNIEnv* env, jclass) {
    LOGI("Game loop stopped");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv* env, jclass) {
    LOGI("Texture initialized");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv* env, jclass, jint texId) {
    // Bind and update your texture here
    LOGI("Texture updated: %d", texId);
}