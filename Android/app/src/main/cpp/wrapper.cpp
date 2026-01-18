// File: wrapper.cpp
// Purpose: JNI bridge + ROM → OTR pipeline owner (Android NDK safe)

#include <jni.h>
#include <vector>
#include <cstdint>
#include <cstring>
#include <android/log.h>
#include <android/asset_manager_jni.h>
#include <cstdio>

#include "otr_builder.h"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ---------------------------------------------------------------------
// Global buffers owned by wrapper
// ---------------------------------------------------------------------
static std::vector<uint8_t> g_rom;
static std::vector<uint8_t> g_otr;
static AAssetManager* g_assetMgr = nullptr;

// ---------------------------------------------------------------------
// Set AssetManager from Java context
// ---------------------------------------------------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_setAssetManager(
        JNIEnv* env,
        jobject /* this */,
        jobject assetManager)
{
    g_assetMgr = AAssetManager_fromJava(env, assetManager);
    LOGI("AssetManager set: %p", g_assetMgr);
}

// ---------------------------------------------------------------------
// Load ROM bytes into memory
// ---------------------------------------------------------------------
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

    const jsize romSize = env->GetArrayLength(romData);
    if (romSize <= 0) {
        LOGE("ROM size invalid");
        return;
    }

    g_rom.resize(static_cast<size_t>(romSize));
    env->GetByteArrayRegion(
        romData,
        0,
        romSize,
        reinterpret_cast<jbyte*>(g_rom.data())
    );

    LOGI("ROM loaded: %d bytes", romSize);
}

// ---------------------------------------------------------------------
// Process ROM → build OTR in memory
// ---------------------------------------------------------------------
extern "C"
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_processRom(
        JNIEnv* env,
        jobject /* this */)
{
    if (g_rom.empty()) {
        LOGE("No ROM loaded");
        return JNI_FALSE;
    }

    if (!g_assetMgr) {
        LOGE("AssetManager not set");
        return JNI_FALSE;
    }

    g_otr.clear();

    const bool success = OTRBuilder::buildOTRForROM(
        g_assetMgr,
        g_rom.data(),
        g_rom.size(),
        g_otr
    );

    if (!success || g_otr.empty()) {
        LOGE("OTR build failed");
        return JNI_FALSE;
    }

    LOGI("OTR build complete: %zu bytes", g_otr.size());
    return JNI_TRUE;
}

// ---------------------------------------------------------------------
// Retrieve OTR as Java byte array
// ---------------------------------------------------------------------
extern "C"
JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getOTRData(
        JNIEnv* env,
        jobject /* this */)
{
    if (g_otr.empty()) {
        LOGE("OTR buffer empty");
        return nullptr;
    }

    jbyteArray out = env->NewByteArray(
        static_cast<jsize>(g_otr.size())
    );

    env->SetByteArrayRegion(
        out,
        0,
        static_cast<jsize>(g_otr.size()),
        reinterpret_cast<const jbyte*>(g_otr.data())
    );

    return out;
}

// ---------------------------------------------------------------------
// Save OTR to file path (optional, convenience)
// ---------------------------------------------------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_saveOTRToFile(
        JNIEnv* env,
        jobject /* this */,
        jstring path)
{
    if (!path || g_otr.empty()) {
        LOGE("Invalid path or empty OTR");
        return;
    }

    const char* cpath = env->GetStringUTFChars(path, nullptr);
    FILE* f = fopen(cpath, "wb");
    if (!f) {
        LOGE("Failed to open file: %s", cpath);
        env->ReleaseStringUTFChars(path, cpath);
        return;
    }

    fwrite(g_otr.data(), 1, g_otr.size(), f);
    fclose(f);
    env->ReleaseStringUTFChars(path, cpath);

    LOGI("OTR saved to: %s", cpath);
}