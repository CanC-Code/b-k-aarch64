#include <jni.h>
#include <android/log.h>
#include <android/asset_manager_jni.h>
#include <thread>
#include <atomic>
#include <vector>
#include <string>
#include <fstream>
#include <sys/stat.h>

#include "otr_generator.hpp"

#define LOG_TAG "BKAWrapper"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ------------------------------
// Global state
// ------------------------------
static std::vector<uint8_t> g_otrData;
static std::atomic<float> g_progress{0.0f};
static std::atomic<bool> g_building{false};

// ------------------------------
// Load YAML from APK assets
// ------------------------------
struct EmbeddedYAML {
    const uint8_t* data;
    size_t size;
};

// Keeps buffer alive while generating
static std::vector<uint8_t> g_yamlBuffer;

EmbeddedYAML loadEmbeddedYAML(AAssetManager* mgr, const char* assetPath) {
    AAsset* asset = AAssetManager_open(mgr, assetPath, AASSET_MODE_STREAMING);
    if (!asset) {
        throw std::runtime_error(std::string("Failed to open YAML asset: ") + assetPath);
    }

    off_t size = AAsset_getLength(asset);
    g_yamlBuffer.resize(size);

    int read = AAsset_read(asset, g_yamlBuffer.data(), size);
    AAsset_close(asset);

    if (read != size) throw std::runtime_error("Failed to read full YAML asset");

    return { g_yamlBuffer.data(), g_yamlBuffer.size() };
}

// ------------------------------
// JNI functions
// ------------------------------
extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processRom(JNIEnv* env, jclass, jobject assetManager, jbyteArray romArray) {
    if (g_building) return;
    g_building = true;
    g_progress = 0.0f;
    g_otrData.clear();

    // Copy ROM data from Java
    jsize romSize = env->GetArrayLength(romArray);
    std::vector<uint8_t> romData(romSize);
    env->GetByteArrayRegion(romArray, 0, romSize, reinterpret_cast<jbyte*>(romData.data()));

    std::thread([romData = std::move(romData), mgr = AAssetManager_fromJava(env, assetManager)]() mutable {
        try {
            OTRGenerator otrGen;
            otrGen.setProgressCallback([](float p) { g_progress = p; });

            // Detect ROM version
            OTRGenerator::RomInfo info;
            if (!OTRGenerator::detectRomVersion(romData.data(), romData.size(), info)) {
                LOGE("Unknown ROM version");
                g_building = false;
                return;
            }

            // Select YAML based on ROM version
            EmbeddedYAML yaml;
            if (info.version == "PAL") {
                yaml = loadEmbeddedYAML(mgr, "otr_yaml/decompressed.pal.yaml");
            } else {
                yaml = loadEmbeddedYAML(mgr, "otr_yaml/decompressed.us.v10.yaml");
            }

            // Generate OTR
            if (!otrGen.generateOTR(romData.data(), romData.size(), 
                                     reinterpret_cast<const char*>(yaml.data), yaml.size, 
                                     g_otrData)) {
                LOGE("OTR generation failed");
            } else {
                LOGI("OTR generation complete, size: %zu bytes", g_otrData.size());
                // Write cache file
                mkdir("/data/data/com.bkawrapper/files", 0755);
                std::ofstream out("/data/data/com.bkawrapper/files/otr_cache.bin", std::ios::binary);
                if(out) out.write(reinterpret_cast<char*>(g_otrData.data()), g_otrData.size());
            }

        } catch (const std::exception& e) {
            LOGE("Exception: %s", e.what());
        }

        g_building = false;
    }).detach();
}

extern "C" JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getOTRProgress(JNIEnv*, jclass) {
    return g_progress;
}

extern "C" JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getOTR(JNIEnv* env, jclass) {
    jbyteArray arr = env->NewByteArray(g_otrData.size());
    if (arr) env->SetByteArrayRegion(arr, 0, g_otrData.size(), reinterpret_cast<jbyte*>(g_otrData.data()));
    return arr;
}