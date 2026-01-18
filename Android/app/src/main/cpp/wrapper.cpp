// File: wrapper.cpp
// Purpose: JNI bridge + ROM → OTR pipeline with progress tracking

#include <jni.h>
#include <vector>
#include <cstdint>
#include <cstring>
#include <android/log.h>
#include <thread>
#include <atomic>

#include "ultra/otr_builder.h"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ---------------------------
// Global buffers / progress
// ---------------------------
static std::vector<uint8_t> g_rom;
static std::vector<uint8_t> g_otr;
static std::atomic<float> g_otr_progress(0.0f);
static std::thread g_otr_thread;

// ---------------------------
// Helper: Run OTR build in background
// ---------------------------
static void runOTRBuild()
{
    g_otr.clear();
    g_otr_progress = 0.0f;

    auto progressCallback = [](float progress, void*) {
        g_otr_progress = progress; // update atomic
    };

    bool success = buildBKOTR(
        g_rom.data(),
        g_rom.size(),
        nullptr,      // optional YAML data pointer (if embedded)
        0,            // optional YAML size
        g_otr,
        progressCallback,
        nullptr       // user data
    );

    if (!success || g_otr.empty()) {
        LOGE("OTR build failed");
        g_otr_progress = 1.0f; // mark complete even if failed
        g_otr.clear();
    } else {
        LOGI("OTR build complete: %zu bytes", g_otr.size());
        g_otr_progress = 1.0f;
    }
}

// ---------------------------
// JNI: Load ROM
// ---------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRom(
        JNIEnv* env,
        jobject /* this */,
        jbyteArray romData)
{
    if (!romData) {
        LOGE("ROM data is null");
        return;
    }

    jsize size = env->GetArrayLength(romData);
    if (size <= 0) {
        LOGE("ROM size invalid");
        return;
    }

    g_rom.resize(static_cast<size_t>(size));
    env->GetByteArrayRegion(
        romData,
        0,
        size,
        reinterpret_cast<jbyte*>(g_rom.data())
    );

    LOGI("ROM loaded: %d bytes", size);
}

// ---------------------------
// JNI: Start processing ROM → OTR
// ---------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processRom(
        JNIEnv*,
        jobject)
{
    // Stop any previous thread
    if (g_otr_thread.joinable()) g_otr_thread.join();

    // Start new background thread
    g_otr_thread = std::thread(runOTRBuild);
}

// ---------------------------
// JNI: Get OTR progress
// ---------------------------
extern "C"
JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getOTRProgress(
        JNIEnv*,
        jobject)
{
    return g_otr_progress.load();
}

// ---------------------------
// JNI: Retrieve OTR data
// ---------------------------
extern "C"
JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getOTRData(
        JNIEnv* env,
        jobject)
{
    if (g_otr.empty()) {
        LOGE("OTR buffer empty");
        return nullptr;
    }

    jbyteArray out = env->NewByteArray(static_cast<jsize>(g_otr.size()));
    env->SetByteArrayRegion(out, 0, static_cast<jsize>(g_otr.size()), reinterpret_cast<const jbyte*>(g_otr.data()));
    return out;
}

// ---------------------------
// JNI: Save OTR to file path (optional convenience)
// ---------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_saveOTRToFile(
        JNIEnv* env,
        jobject,
        jstring path)
{
    if (g_otr.empty()) {
        LOGE("OTR buffer empty");
        return;
    }

    const char* cpath = env->GetStringUTFChars(path, nullptr);
    FILE* f = fopen(cpath, "wb");
    if (!f) {
        LOGE("Failed to open file for writing: %s", cpath);
        env->ReleaseStringUTFChars(path, cpath);
        return;
    }

    fwrite(g_otr.data(), 1, g_otr.size(), f);
    fclose(f);
    env->ReleaseStringUTFChars(path, cpath);
    LOGI("OTR saved to %s", cpath);
}

// ---------------------------
// TODO: Implement remaining game loop, texture, and Surface JNI calls
// ---------------------------