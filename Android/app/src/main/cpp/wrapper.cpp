// File: wrapper.cpp
// Purpose: JNI bridge + ROM → OTR pipeline (NDK + Android assets safe)

#include <jni.h>
#include <vector>
#include <cstdint>
#include <cstring>
#include <android/log.h>
#include <android/asset_manager_jni.h>

#include "ultra/otr_builder.h"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Global buffers owned by wrapper
static std::vector<uint8_t> g_rom;
static std::vector<uint8_t> g_otr;
static AAssetManager* g_assetMgr = nullptr;

extern "C" {

// ----------------------------------------
// Set the Android AssetManager
// ----------------------------------------
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_setAssetManager(
        JNIEnv* env,
        jobject /* this */,
        jobject mgr)
{
    g_assetMgr = AAssetManager_fromJava(env, mgr);
    if (!g_assetMgr) LOGE("Failed to obtain AAssetManager");
    else LOGI("AssetManager set");
}

// ----------------------------------------
// Load ROM bytes
// ----------------------------------------
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_loadRom(
        JNIEnv* env,
        jobject /* this */,
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

    LOGI("ROM loaded: %d bytes", romSize);
    return JNI_TRUE;
}

// ----------------------------------------
// Build OTR from ROM + embedded YAML
// ----------------------------------------
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_processRom(
        JNIEnv* /* env */,
        jobject /* this */)
{
    if (!g_assetMgr) {
        LOGE("AssetManager not set");
        return JNI_FALSE;
    }
    if (g_rom.empty()) {
        LOGE("ROM buffer empty");
        return JNI_FALSE;
    }

    g_otr.clear();

    bool success = OTRBuilder::buildOTRForROM(
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

// ----------------------------------------
// Retrieve OTR bytes
// ----------------------------------------
JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getOTR(
        JNIEnv* env,
        jobject /* this */)
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

} // extern "C"