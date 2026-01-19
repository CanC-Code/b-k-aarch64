#include <jni.h>
#include <android/log.h>
#include <android/asset_manager_jni.h>
#include <GLES2/gl2.h>
#include <thread>
#include <atomic>
#include <vector>
#include <string>
#include <fstream>
#include <sys/stat.h>
#include "otr_generator.hpp"
#include "otr_assets.hpp"

#undef LOG_TAG
#define LOG_TAG "BKAWrapper"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

static std::vector<uint8_t> g_otrData;
static std::vector<uint8_t> g_romData;
static std::atomic<float> g_progress{0.0f};
static std::atomic<bool> g_building{false};

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRomFromUri(JNIEnv* env, jclass, jobject resolver, jobject uri) {
    g_romData.clear();
    g_progress = 0.0f;
    g_building = true;

    // Load ROM bytes here into g_romData...
}

extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processRom(JNIEnv* env, jclass) {
    if (!g_building) return;

    std::thread([](){
        try {
            g_progress = 0.0f;
            OTRGenerator otrGen;

            std::vector<std::pair<std::string, std::vector<uint8_t>>> yamlAssets = {
                {"decompressed.pal.yaml", std::vector<uint8_t>(embedded_pal_yaml, embedded_pal_yaml + embedded_pal_yaml_size)},
                {"decompressed.us.v10.yaml", std::vector<uint8_t>(embedded_us_yaml, embedded_us_yaml + embedded_us_yaml_size)}
            };

            otrGen.generate(yamlAssets, g_romData, [&](float progress){
                g_progress = progress;
            });

            g_otrData = otrGen.getData();

            mkdir("/data/data/com.bkawrapper/files", 0755);
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