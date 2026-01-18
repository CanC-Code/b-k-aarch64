// File: wrapper.cpp
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

// OpenGL texture
static std::mutex g_texMutex;
static GLuint g_textureId = 0;

// Cached OTR path
static const std::string kOTRCachePath = "/data/data/com.bkawrapper/files/otr_cache.bin";

// -----------------------------
// Helpers: File caching
// -----------------------------
static bool fileExists(const std::string& path) {
    struct stat buffer{};
    return (stat(path.c_str(), &buffer) == 0);
}

static bool saveOTRToDisk(const std::string& path, const std::vector<uint8_t>& data) {
    std::ofstream out(path, std::ios::binary);
    if (!out.is_open()) return false;
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
// JNI: loadRom
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
// JNI: processRom (async)
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

    if (!g_assetManager) {
        LOGE("AssetManager not set, cannot load YAML");
        return;
    }

    if (g_building.exchange(true)) {
        LOGE("OTR build already in progress");
        return;
    }

    std::thread([]() {
        LOGI("OTR build thread started");

        // Load cached OTR first
        if (loadOTRFromDisk(kOTRCachePath, g_otr)) {
            g_progress.store(1.0f);
            g_building.store(false);
            LOGI("Using cached OTR");
            // Auto upload texture
            {
                std::lock_guard<std::mutex> lock(g_texMutex);
                if (g_textureId == 0) glGenTextures(1, &g_textureId);
                glBindTexture(GL_TEXTURE_2D, g_textureId);
                const int width = 256, height = 256;
                if (g_otr.size() >= width * height * 4) {
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                                 GL_RGBA, GL_UNSIGNED_BYTE, g_otr.data());
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
                    LOGI("OTR texture auto-initialized (ID=%u)", g_textureId);
                }
            }
            return;
        }

        g_progress.store(0.05f);

        // Detect ROM version
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

        // Generate OTR
        OTRGenerator generator;
        generator.setProgressCallback([](float progress) {
            g_progress.store(progress);
        });

        std::vector<uint8_t> localOTR;
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
            saveOTRToDisk(kOTRCachePath, g_otr);

            // Upload as OpenGL texture
            {
                std::lock_guard<std::mutex> lock(g_texMutex);
                if (g_textureId == 0) glGenTextures(1, &g_textureId);
                glBindTexture(GL_TEXTURE_2D, g_textureId);
                const int width = 256, height = 256;
                if (g_otr.size() >= width * height * 4) {
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                                 GL_RGBA, GL_UNSIGNED_BYTE, g_otr.data());
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
                    LOGI("OTR texture generated and uploaded (ID=%u)", g_textureId);
                }
            }

            g_progress.store(1.0f);
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

// -----------------------------
// JNI: getOTR
// -----------------------------
extern "C"
JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getOTR(
        JNIEnv* env,
        jclass)
{
    std::lock_guard<std::mutex> lock(g_mutex);
    if (g_otr.empty()) return nullptr;

    jbyteArray arr = env->NewByteArray(g_otr.size());
    if (!arr) return nullptr;

    env->SetByteArrayRegion(arr, 0, g_otr.size(), reinterpret_cast<const jbyte*>(g_otr.data()));
    return arr;
}

// -----------------------------
// Rendering / lifecycle
// -----------------------------
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initGame(JNIEnv*, jclass, jobject surface) {
    // Implement native game init
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv*, jclass) {
    // Optional standard texture init
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initTextureWithOTR(JNIEnv*, jclass, jbyteArray) {
    // Already handled automatically after OTR generation
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv*, jclass, jint textureId) {
    std::lock_guard<std::mutex> lock(g_texMutex);
    if (g_textureId != 0) glBindTexture(GL_TEXTURE_2D, g_textureId);
}

extern "C"
JNIEXPORT jint JNICALL
Java_com_bkawrapper_NativeBridge_getTextureId(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> lock(g_texMutex);
    return g_textureId;
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_startGameLoop(JNIEnv*, jclass) {}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_stopGameLoop(JNIEnv*, jclass) {}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv*, jclass) {
    std::lock_guard<std::mutex> lock(g_texMutex);
    if (g_textureId != 0) {
        glDeleteTextures(1, &g_textureId);
        g_textureId = 0;
    }
}