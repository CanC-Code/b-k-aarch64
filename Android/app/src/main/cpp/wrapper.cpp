// File: wrapper.cpp
// Purpose: JNI bridge + ROM → OTR pipeline with real YAML parsing and progress

#include <jni.h>
#include <vector>
#include <cstdint>
#include <cstring>
#include <functional>
#include <atomic>
#include <android/log.h>
#include <android/asset_manager_jni.h>
#include "otr_builder.h"
#include "otr_generator.h"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ---------------------------
// Global buffers / state
// ---------------------------
static std::vector<uint8_t> g_rom;
static std::vector<uint8_t> g_otr;
static std::atomic<float> g_progress(0.0f);

// ---------------------------
// Progress callback
// ---------------------------
static void progressCallback(float progress) {
    g_progress.store(progress);
}

// ---------------------------
// JNI functions
// ---------------------------
extern "C" JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_loadRom(
        JNIEnv* env,
        jobject /* this */,
        jbyteArray romData)
{
    if (!romData) {
        LOGE("ROM data is null");
        return JNI_FALSE;
    }

    jsize romSize = env->GetArrayLength(romData);
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

    LOGI("ROM loaded: %d bytes", romSize);
    g_otr.clear();
    g_progress.store(0.0f);

    return JNI_TRUE;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_processRom(
        JNIEnv* env,
        jobject /* this */,
        jobject assetManager)
{
    if (g_rom.empty()) {
        LOGE("ROM not loaded");
        return JNI_FALSE;
    }

    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    if (!mgr) {
        LOGE("Invalid AssetManager");
        return JNI_FALSE;
    }

    g_otr.clear();
    g_progress.store(0.0f);

    bool success = buildOTRForROM(mgr, g_rom.data(), g_rom.size(), g_otr);
    if (!success) {
        LOGE("OTR generation failed");
        return JNI_FALSE;
    }

    g_progress.store(1.0f);
    LOGI("OTR generation complete: %zu bytes", g_otr.size());
    return JNI_TRUE;
}

extern "C" JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getOTRProgress(
        JNIEnv* env,
        jobject /* this */)
{
    return g_progress.load();
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getOTRData(
        JNIEnv* env,
        jobject /* this */)
{
    if (g_otr.empty()) return nullptr;

    jbyteArray out = env->NewByteArray(static_cast<jsize>(g_otr.size()));
    env->SetByteArrayRegion(
        out,
        0,
        static_cast<jsize>(g_otr.size()),
        reinterpret_cast<const jbyte*>(g_otr.data())
    );

    return out;
}

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_saveOTRToFile(
        JNIEnv* env,
        jobject /* this */,
        jstring path)
{
    if (g_otr.empty()) {
        LOGE("OTR empty, cannot save");
        return;
    }

    const char* cpath = env->GetStringUTFChars(path, nullptr);
    if (!cpath) return;

    FILE* f = fopen(cpath, "wb");
    if (!f) {
        LOGE("Failed to open file: %s", cpath);
        env->ReleaseStringUTFChars(path, cpath);
        return;
    }

    fwrite(g_otr.data(), 1, g_otr.size(), f);
    fclose(f);
    env->ReleaseStringUTFChars(path, cpath);

    LOGI("OTR saved to %s", cpath);
}