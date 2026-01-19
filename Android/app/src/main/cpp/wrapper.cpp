#include <jni.h>
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
static std::vector<uint8_t> g_otrData;
static std::atomic<float> g_progress{0.0f};
static std::atomic<bool> g_building{false};

// ------------------------------
// JNI functions
// ------------------------------
extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRomFromUri(JNIEnv* env, jclass, jobject resolver, jobject uri) {
    // Clear previous ROM data and reset progress
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

            // Initialize generator with embedded YAML assets
            OTRGenerator otrGen(&embedded_assets); // embedded_assets is from otr_assets.hpp

            // Build OTR data with progress callback
            g_otrData = otrGen.buildOTR([&](float progress){
                g_progress = progress;
            });

            // Ensure cache directory exists
            mkdir("/data/data/com.bkawrapper/files", 0755);

            // Write OTR cache file
            std::ofstream out("/data/data/com.bkawrapper/files/otr_cache.bin", std::ios::binary);
            if(out) out.write(reinterpret_cast<char*>(g_otrData.data()), g_otrData.size());
            out.close();

            LOGI("OTR generation complete, size: %zu bytes", g_otrData.size());

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
    if (arr) env->SetByteArrayRegion(arr, 0, g_otrData.size(), reinterpret_cast<jbyte*>(g_otrData.data()));
    return arr;
}