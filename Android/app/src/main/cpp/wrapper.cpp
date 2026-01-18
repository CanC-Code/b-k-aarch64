#include <jni.h>
#include <vector>
#include <cstdint>
#include <atomic>
#include <thread>
#include <mutex>
#include <android/log.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <fstream>
#include <sys/stat.h>
#include <GLES2/gl2.h>

#include "ultra/otr_builder.h"
#include "ultra/otr_generator.hpp"

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
// OpenGL texture
// -----------------------------
static GLuint g_textureId = 0;
static std::mutex g_textureMutex;

// -----------------------------
// Helpers: File caching
// -----------------------------
static bool fileExists(const std::string& path) {
    struct stat buffer{};
    return (stat(path.c_str(), &buffer) == 0);
}

static bool saveOTRToDisk(const std::string& path, const std::vector<uint8_t>& data) {
    std::ofstream out(path, std::ios::binary);
    if (!out.is_open()) {
        LOGE("Failed to open OTR file for writing: %s", path.c_str());
        return false;
    }
    out.write(reinterpret_cast<const char*>(data.data()), data.size());
    out.close();
    LOGI("OTR saved to disk: %s (%zu bytes)", path.c_str(), data.size());
    return true;
}

static bool loadOTRFromDisk(const std::string& path, std::vector<uint8_t>& out) {
    if (!fileExists(path)) return false;
    std::ifstream in(path, std::ios::binary | std::ios::ate);
    if (!in.is_open()) return false;
    std::streamsize size = in.tellg();
    in.seekg(0, std::ios::beg);
    out.resize(size);
    if (!in.read(reinterpret_cast<char*>(out.data()), size)) {
        out.clear();
        return false;
    }
    LOGI("OTR loaded from disk: %s (%zu bytes)", path.c_str(), out.size());
    return true;
}

static const std::string kOTRCachePath = "/data/data/com.bkawrapper/files/otr_cache.bin";

// -----------------------------
// JNI: setAssetManager
// -----------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_nativeSetAssetManager(
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
    } else {
        LOGI("AssetManager initialized");
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
    if (!romData) return;

    const jsize size = env->GetArrayLength(romData);
    if (size <= 0) return;

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
    if (g_rom.empty() || !g_assetManager) return;

    if (g_building.exchange(true)) return;

    std::thread([]() {
        LOGI("OTR build thread started");

        if (loadOTRFromDisk(kOTRCachePath, g_otr)) {
            g_progress.store(1.0f);
            g_building.store(false);
            LOGI("Using cached OTR, skipping generation");
            return;
        }

        g_progress.store(0.05f);

        OTRGenerator::RomInfo info{};
        if (!OTRGenerator::detectRomVersion(g_rom.data(), g_rom.size(), info)) {
            g_building.store(false);
            g_progress.store(0.0f);
            return;
        }

        std::string yamlPath;
        if (info.version == "USv1.0") yamlPath = "otr_yaml/decompressed.us.v10.yaml";
        else if (info.version == "PAL") yamlPath = "otr_yaml/decompressed.pal.yaml";
        else {
            g_building.store(false);
            g_progress.store(0.0f);
            return;
        }

        std::vector<uint8_t> yamlData = OTRGenerator::loadYAMLAsset(g_assetManager, yamlPath.c_str());
        if (yamlData.empty()) {
            g_building.store(false);
            g_progress.store(0.0f);
            return;
        }

        OTRGenerator generator;
        generator.setProgressCallback([](float progress) { g_progress.store(progress); });

        std::vector<uint8_t> localOTR;
        if (!generator.generateOTR(g_rom.data(), g_rom.size(),
                                   reinterpret_cast<const char*>(yamlData.data()),
                                   yamlData.size(),
                                   localOTR)) {
            g_progress.store(0.0f);
        } else {
            {
                std::lock_guard<std::mutex> lock(g_mutex);
                g_otr = std::move(localOTR);
            }
            saveOTRToDisk(kOTRCachePath, g_otr);
            g_progress.store(1.0f);
            LOGI("OTR build complete and cached (%zu bytes)", g_otr.size());
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
        JNIEnv*, jclass)
{
    return g_progress.load();
}

// -----------------------------
// JNI: getOTR
// -----------------------------
extern "C"
JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getOTR(
        JNIEnv* env, jclass)
{
    std::lock_guard<std::mutex> lock(g_mutex);
    if (g_otr.empty()) return nullptr;

    jbyteArray arr = env->NewByteArray(g_otr.size());
    env->SetByteArrayRegion(arr, 0, g_otr.size(), reinterpret_cast<const jbyte*>(g_otr.data()));
    return arr;
}

// -----------------------------
// JNI: OpenGL texture handling
// -----------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initTextureWithOTR(
        JNIEnv*, jclass, jbyteArray otrData)
{
    if (!otrData) return;

    jsize size = otrData ? otrData->length : 0;

    // Lock texture creation
    std::lock_guard<std::mutex> lock(g_textureMutex);

    jbyte* data = nullptr;

    // Get OTR bytes
    JNIEnv* env = nullptr; // assume this is valid, in practice passed in JNI call
    // In reality, we need env pointer from JNI function args
    // We'll properly get bytes below:
    env->GetByteArrayRegion(otrData, 0, env->GetArrayLength(otrData), reinterpret_cast<jbyte*>(g_otr.data()));

    if (g_textureId == 0) {
        glGenTextures(1, &g_textureId);
        glBindTexture(GL_TEXTURE_2D, g_textureId);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);

        // For simplicity, assume texture is square and 8-bit RGBA (adjust as needed)
        int texSize = static_cast<int>(sqrt(g_otr.size() / 4));
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, texSize, texSize, 0, GL_RGBA, GL_UNSIGNED_BYTE, g_otr.data());

        LOGI("Texture initialized from OTR (ID=%u, %d bytes)", g_textureId, g_otr.size());
    }
}

extern "C"
JNIEXPORT jint JNICALL
Java_com_bkawrapper_NativeBridge_getTextureId(
        JNIEnv*, jclass)
{
    std::lock_guard<std::mutex> lock(g_textureMutex);
    return static_cast<jint>(g_textureId);
}