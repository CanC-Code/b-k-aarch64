#include <jni.h>
#include <android/asset_manager_jni.h>
#include <android/log.h>
#include <vector>
#include <string>
#include <cstring>
#include "otr_generator.hpp"
#include "embedded_data.hpp"

#define LOG_TAG "NativeBridge"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Global OTR generator
static OTRGenerator gOTRGenerator;

// JNI Helper: call Java progress callback
void reportProgressToJava(JNIEnv* env, jobject progressCallback, float p) {
    if (!progressCallback) return;

    jclass cls = env->GetObjectClass(progressCallback);
    if (!cls) return;

    jmethodID mid = env->GetMethodID(cls, "onProgress", "(F)V");
    if (!mid) return;

    env->CallVoidMethod(progressCallback, mid, p);
}

// Main JNI entry
extern "C"
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_loadEmbeddedOTRAssets(
        JNIEnv* env,
        jclass clazz,
        jobject context,
        jobject assetManager,
        jobject progressCallback
) {
    (void)clazz;
    (void)context;

    try {
        // Select YAML based on embedded ROM version
        OTRGenerator::RomInfo info;
        if (!OTRGenerator::detectRomVersion(embedded_rom, embedded_rom_size, info)) {
            LOGE("Failed to detect embedded ROM version");
            return JNI_FALSE;
        }

        const uint8_t* yamlData = nullptr;
        size_t yamlSize = 0;

        if (info.version.find("US") != std::string::npos) {
            yamlData = embedded_us_yaml;
            yamlSize = embedded_us_yaml_size;
        } else {
            yamlData = embedded_pal_yaml;
            yamlSize = embedded_pal_yaml_size;
        }

        std::vector<uint8_t> outOTR;
        gOTRGenerator.setProgressCallback([env, progressCallback](float p) {
            reportProgressToJava(env, progressCallback, p);
        });

        if (!gOTRGenerator.generateOTR(embedded_rom, embedded_rom_size, 
                                       reinterpret_cast<const char*>(yamlData), yamlSize,
                                       outOTR)) {
            LOGE("OTR generation failed");
            return JNI_FALSE;
        }

        LOGI("OTR generated successfully: %zu bytes", outOTR.size());

        // TODO: optionally write outOTR to file if you want to load later
        return JNI_TRUE;

    } catch (const std::exception& e) {
        LOGE("Exception: %s", e.what());
        return JNI_FALSE;
    } catch (...) {
        LOGE("Unknown error during OTR generation");
        return JNI_FALSE;
    }
}