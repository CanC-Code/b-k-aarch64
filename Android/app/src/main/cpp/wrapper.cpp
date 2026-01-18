#include <jni.h>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <GLES2/gl2.h>
#include <thread>
#include <atomic>
#include <vector>
#include <string>
#include <fstream>
#include <sys/stat.h>

#include "otr_generator.hpp"
#include "otr_assets.hpp"

#define LOG_TAG "BKAWrapper"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ------------------------------
// Global state
// ------------------------------
static AAssetManager* g_assetManager = nullptr;
static std::vector<uint8_t> g_otrData;
static std::atomic<float> g_progress{0.0f};
static std::atomic<bool> g_building{false};

// ------------------------------
// JNI functions
// ------------------------------
extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_setAssetManager(JNIEnv* env, jclass, jobject mgr) {
    g_assetManager = AAssetManager_fromJava(env, mgr);
    LOGI("AssetManager set: %p", g_assetManager);
}

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRomFromUri(JNIEnv* env, jclass, jobject resolver, jobject uri) {
    // Dummy: store ROM data in memory
    // Actual ROM read is handled elsewhere
    g_otrData.clear();
    g_progress = 0.0f;
    g_building = true;
}

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processRom(JNIEnv* env, jclass) {
    if (!g_building) return;
    std::thread([](){
        try {
            g_progress = 0.0f;

            // Load embedded YAMLs
            OTRGenerator otrGen;
            otrGen.loadEmbeddedYAML("pal", embedded_pal_yaml, embedded_pal_size);
            otrGen.loadEmbeddedYAML("us.v10", embedded_us_yaml, embedded_us_size);

            // Generate OTR
            otrGen.generate([&](float progress){
                g_progress = progress;
            });

            // Copy generated data to global
            g_otrData = otrGen.getData();

            // Optionally write cache safely
            mkdir("/data/data/com.bkawrapper/files", 0755);
            std::ofstream out("/data/data/com.bkawrapper/files/otr_cache.bin", std::ios::binary);
            if(out) out.write((char*)g_otrData.data(), g_otrData.size());
            out.close();

        } catch (const std::exception& e) {
            LOGE("OTR generation failed: %s", e.what());
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
    if (arr) env->SetByteArrayRegion(arr, 0, g_otrData.size(), (jbyte*)g_otrData.data());
    return arr;
}