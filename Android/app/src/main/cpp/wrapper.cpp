#include <jni.h>
#include <vector>
#include <cstdint>
#include <cstring>
#include <atomic>
#include <thread>
#include <mutex>
#include <android/log.h>
#include <android/asset_manager_jni.h>

#include "otr_builder.h"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// --------------------
// Global buffers & state
// --------------------
static std::vector<uint8_t> g_rom;
static std::vector<uint8_t> g_otr;

static std::atomic<float> g_otr_progress{0.0f};
static std::mutex g_otr_mutex;
static bool g_generating = false;

// --------------------
// Threaded OTR generation
// --------------------
static void generateOTRThread(AAssetManager* mgr) {
    {
        std::lock_guard<std::mutex> lock(g_otr_mutex);
        g_otr.clear();
        g_otr_progress = 0.0f;
        g_generating = true;
    }

    bool ok = buildOTRForROM(
        mgr,
        g_rom.data(),
        g_rom.size(),
        g_otr,
        [](float progress) {
            g_otr_progress = progress;
        }
    );

    if (!ok) {
        LOGE("OTR generation failed");
        std::lock_guard<std::mutex> lock(g_otr_mutex);
        g_otr.clear();
        g_otr_progress = 0.0f;
    } else {
        LOGI("OTR generation complete: %zu bytes", g_otr.size());
        g_otr_progress = 1.0f;
    }

    g_generating = false;
}

// --------------------
// JNI interface
// --------------------
extern "C"
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_processRom(
        JNIEnv* env,
        jobject /* this */,
        jobject assetManager,
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

    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    if (!mgr) {
        LOGE("Failed to get AAssetManager");
        return JNI_FALSE;
    }

    // Start generation in a separate thread
    std::thread(generateOTRThread, mgr).detach();
    return JNI_TRUE;
}

extern "C"
JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getOTRProgress(
        JNIEnv* /* env */,
        jobject /* this */)
{
    return g_otr_progress.load();
}

extern "C"
JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getOTR(
        JNIEnv* env,
        jobject /* this */)
{
    std::lock_guard<std::mutex> lock(g_otr_mutex);

    if (g_otr.empty()) {
        LOGE("OTR buffer empty");
        return nullptr;
    }

    jbyteArray out = env->NewByteArray(static_cast<jsize>(g_otr.size()));
    env->SetByteArrayRegion(
        out,
        0,
        static_cast<jsize>(g_otr.size()),
        reinterpret_cast<const jbyte*>(g_otr.data())
    );
    return out;
}