#include <jni.h>
#include <android/log.h>
#include <thread>
#include <atomic>
#include <vector>
#include <fstream>

#include "otr_generator.hpp"
#include "otr_assets.hpp"

#define LOG_TAG "BKAWrapper"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ------------------------------
// Global state
// ------------------------------
static std::vector<uint8_t> g_otrData;
static std::atomic<float> g_progress{0.0f};
static std::atomic<bool> g_building{false};
static AAssetManager* g_assetMgr = nullptr;

// ------------------------------
// JNI functions
// ------------------------------
extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_setAssetManager(JNIEnv* env, jclass, jobject mgr) {
    g_assetMgr = AAssetManager_fromJava(env, mgr);
}

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processRom(JNIEnv*, jclass) {
    if (!g_building && g_assetMgr) {
        g_building = true;
        g_progress = 0.0f;

        std::thread([](){
            try {
                g_otrData.clear();

                OTRGenerator otrGen;
                otrGen.setProgressCallback([](float p){ g_progress = p; });

                // Load dynamic assets
                auto assets = loadEmbeddedOTRAssets(g_assetMgr);
                for (auto& asset : assets) {
                    otrGen.loadEmbeddedYAML(asset.name.c_str(), asset.data.data(), asset.data.size());
                }

                // Generate OTR
                otrGen.generate([&](float progress){ g_progress = progress; });

                g_otrData = otrGen.getData();

                // Write cache
                mkdir("/data/data/com.bkawrapper/files", 0755);
                std::ofstream out("/data/data/com.bkawrapper/files/otr_cache.bin", std::ios::binary);
                if(out) out.write(reinterpret_cast<char*>(g_otrData.data()), g_otrData.size());
                out.close();

                LOGI("OTR generation complete, size: %zu bytes", g_otrData.size());

            } catch (const std::exception& e) {
                LOGE("OTR generation failed: %s", e.what());
            } catch (...) {
                LOGE("OTR generation unknown failure");
            }
            g_building = false;
        }).detach();
    }
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