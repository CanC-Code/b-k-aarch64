#include <jni.h>
#include <android/log.h>
#include <GLES2/gl2.h>
#include <thread>
#include <atomic>
#include <vector>
#include <string>
#include <fstream>
#include <sys/stat.h>
#include <android/asset_manager_jni.h>

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
// JNI functions
// ------------------------------
extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processRom(JNIEnv* env, jclass, jobject assetManager, jbyteArray romArray) {
    if (g_building) return;

    g_otrData.clear();
    g_progress = 0.0f;
    g_building = true;

    // Copy ROM from Java byte array
    jsize romSize = env->GetArrayLength(romArray);
    std::vector<uint8_t> romData(romSize);
    env->GetByteArrayRegion(romArray, 0, romSize, reinterpret_cast<jbyte*>(romData.data()));

    // Launch generation thread
    std::thread([romData = std::move(romData), assetManagerGlobal = assetManager]() mutable {
        try {
            // Wrap asset manager
            AAssetManager* mgr = AAssetManager_fromJava(env, assetManagerGlobal);
            if (!mgr) throw std::runtime_error("Failed to get AAssetManager");

            // Load YAMLs dynamically
            std::vector<std::pair<std::string, std::vector<uint8_t>>> yamlAssets;
            struct { const char* name; } yamlFiles[] = {
                {"otr_yaml/decompressed.pal.yaml"},
                {"otr_yaml/decompressed.us.v10.yaml"}
            };

            for (auto& yf : yamlFiles) {
                std::vector<uint8_t> data = OTRGenerator::loadYAMLAsset(mgr, yf.name);
                if (!data.empty()) {
                    yamlAssets.emplace_back(yf.name, std::move(data));
                    LOGI("Loaded YAML asset: %s (%zu bytes)", yf.name, yamlAssets.back().second.size());
                } else {
                    LOGE("Failed to load YAML asset: %s", yf.name);
                }
            }

            // Initialize generator
            OTRGenerator otrGen;
            otrGen.setProgressCallback([](float progress){ g_progress = progress; });

            if (!otrGen.generate(romData.data(), romData.size(), yamlAssets)) {
                LOGE("OTR generation failed");
            } else {
                g_otrData = otrGen.getData();

                // Write cache
                mkdir("/data/data/com.bkawrapper/files", 0755);
                std::ofstream out("/data/data/com.bkawrapper/files/otr_cache.bin", std::ios::binary);
                if (out) out.write(reinterpret_cast<char*>(g_otrData.data()), g_otrData.size());

                LOGI("OTR generation complete, size: %zu bytes", g_otrData.size());
            }

        } catch (const std::exception& e) {
            LOGE("Exception in OTR thread: %s", e.what());
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