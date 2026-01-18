#include <jni.h>
#include <vector>
#include <cstdint>
#include <atomic>
#include <thread>
#include <mutex>
#include <android/log.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>

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

static AAssetManager* g_assetManager = nullptr;

// -----------------------------
// JNI: setAssetManager
// -----------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_setAssetManager(
        JNIEnv* env,
        jclass,
        jobject assetManager) {

    if (!assetManager) {
        LOGE("AssetManager is null");
        g_assetManager = nullptr;
        return;
    }

    g_assetManager = AAssetManager_fromJava(env, assetManager);
    if (!g_assetManager) {
        LOGE("Failed to get native AAssetManager");
    }
}

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
    env->GetByteArrayRegion(romData, 0, size, reinterpret_cast<jbyte*>(g_rom.data()));

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

        // Determine YAML path
        OTRGenerator::RomInfo info{};
        if (!OTRGenerator::detectRomVersion(g_rom.data(), g_rom.size(), info)) {
            LOGE("ROM version detection failed");
            g_building.store(false);
            g_progress.store(0.0f);
            return;
        }

        std::string yamlPath;
        if (info.version == "USv1.0") yamlPath = "otr_yaml/decompressed.us.v10.yaml";
        else if (info.version == "PAL") yamlPath = "otr_yaml/decompressed.pal.yaml";
        else {
            LOGE("Unsupported ROM version");
            g_building.store(false);
            g_progress.store(0.0f);
            return;
        }

        std::vector<uint8_t> yamlData =
            OTRGenerator::loadYAMLAsset(g_assetManager, yamlPath.c_str());

        if (yamlData.empty()) {
            LOGE("Failed to load YAML asset: %s", yamlPath.c_str());
            g_building.store(false);
            g_progress.store(0.0f);
            return;
        }

        OTRGenerator generator;
        if (!generator.generateOTR(g_rom.data(), g_rom.size(),
                                   reinterpret_cast<const char*>(yamlData.data()),
                                   yamlData.size(),
                                   localOTR)) {
            LOGE("OTR generation failed");
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
// JNI: getOTRProgress
// -----------------------------
extern "C"
JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getOTRProgress(
        JNIEnv*,
        jclass)
{
    return g_progress.load();
}