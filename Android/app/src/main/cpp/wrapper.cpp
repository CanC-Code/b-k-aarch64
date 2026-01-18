#include <jni.h>
#include <vector>
#include <atomic>
#include <thread>
#include <mutex>

#include <android/log.h>

#include "ultra/otr_builder.h"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,  LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// -----------------------------
// Global state
// -----------------------------
static std::vector<uint8_t> g_rom;
static std::vector<uint8_t> g_otr;

static std::atomic<float> g_progress{0.0f};
static std::atomic<bool>  g_building{false};
static std::mutex         g_mutex;

// -----------------------------
// JNI: loadRom(byte[])
// -----------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRom(
        JNIEnv* env,
        jclass,
        jbyteArray romData)
{
    if (!romData) {
        LOGE("loadRom: null byte array");
        return;
    }

    const jsize size = env->GetArrayLength(romData);
    if (size <= 0) {
        LOGE("loadRom: invalid size");
        return;
    }

    std::lock_guard<std::mutex> lock(g_mutex);

    g_rom.resize(size);
    env->GetByteArrayRegion(
        romData,
        0,
        size,
        reinterpret_cast<jbyte*>(g_rom.data())
    );

    g_otr.clear();
    g_progress.store(0.0f);
    g_building.store(false);

    LOGI("ROM loaded (%d bytes)", size);
}

// -----------------------------
// JNI: processRom()
// -----------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processRom(
        JNIEnv*,
        jclass)
{
    if (g_rom.empty()) {
        LOGE("processRom called with no ROM loaded");
        return;
    }

    if (g_building.exchange(true)) {
        LOGE("OTR build already in progress");
        return;
    }

    std::thread([]() {
        LOGI("OTR build thread started");

        g_progress.store(0.05f);

        std::vector<uint8_t> localOTR;

        const bool success = buildOTRForROM(
            nullptr,            // AssetManager not required
            g_rom.data(),
            g_rom.size(),
            localOTR
        );

        if (!success || localOTR.empty()) {
            LOGE("OTR build failed");
            g_progress.store(0.0f);
        } else {
            {
                std::lock_guard<std::mutex> lock(g_mutex);
                g_otr = std::move(localOTR);
            }
            g_progress.store(1.0f);
            LOGI("OTR build complete (%zu bytes)", g_otr.size());
        }

        g_building.store(false);
    }).detach();
}

// -----------------------------
// JNI: getOTRProgress()
// -----------------------------
extern "C"
JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getOTRProgress(
        JNIEnv*,
        jclass)
{
    return g_progress.load();
}