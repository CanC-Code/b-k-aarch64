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

#define LOG_TAG "BKAWrapper"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ------------------------------
// Global state
// ------------------------------
static std::vector<uint8_t> g_otrData;
static std::atomic<float> g_progress{0.0f};
static std::atomic<bool> g_building{false};
static std::vector<uint8_t> g_romData;

// ------------------------------
// JNI: load ROM bytes from URI
// ------------------------------
extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRomFromUri(JNIEnv* env, jclass, jobject resolver, jobject uri) {
    g_otrData.clear();
    g_romData.clear();
    g_progress = 0.0f;
    g_building = true;

    // Read bytes via Java ContentResolver
    jclass resolverClass = env->GetObjectClass(resolver);
    jmethodID openStream = env->GetMethodID(resolverClass, "openInputStream", "(Landroid/net/Uri;)Ljava/io/InputStream;");
    jobject stream = env->CallObjectMethod(resolver, openStream, uri);
    if (!stream) {
        LOGE("Failed to open ROM stream");
        g_building = false;
        return;
    }

    jclass streamClass = env->GetObjectClass(stream);
    jmethodID available = env->GetMethodID(streamClass, "available", "()I");
    jmethodID read = env->GetMethodID(streamClass, "read", "([B)I");
    jmethodID close = env->GetMethodID(streamClass, "close", "()V");

    jint size = env->CallIntMethod(stream, available);
    if (size <= 0) {
        LOGE("Empty ROM");
        env->CallVoidMethod(stream, close);
        g_building = false;
        return;
    }

    jbyteArray buffer = env->NewByteArray(size);
    jint readBytes = env->CallIntMethod(stream, read, buffer);
    if (readBytes != size) {
        LOGE("Failed to read full ROM (read %d of %d)", readBytes, size);
        env->CallVoidMethod(stream, close);
        g_building = false;
        return;
    }

    g_romData.resize(size);
    env->GetByteArrayRegion(buffer, 0, size, reinterpret_cast<jbyte*>(g_romData.data()));
    env->CallVoidMethod(stream, close);

    LOGI("ROM loaded: %d bytes", size);
}

// ------------------------------
// JNI: process ROM into OTR
// ------------------------------
extern "C" JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processRom(JNIEnv* env, jclass, jobject assetManager) {
    if (!g_building || g_romData.empty()) return;

    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    if (!mgr) {
        LOGE("Invalid asset manager");
        g_building = false;
        return;
    }

    std::thread([](AAssetManager* mgr){
        try {
            g_progress = 0.0f;

            OTRGenerator otrGen;
            otrGen.setProgressCallback([](float p){ g_progress = p; });

            // Load YAMLs dynamically
            auto palYaml = OTRGenerator::loadYAMLAsset(mgr, "otr_yaml/decompressed.pal.yaml");
            auto usYaml  = OTRGenerator::loadYAMLAsset(mgr, "otr_yaml/decompressed.us.v10.yaml");

            // Choose which YAML to use based on ROM version
            OTRGenerator::RomInfo info;
            std::vector<uint8_t>* chosenYaml = &usYaml;
            if (OTRGenerator::detectRomVersion(g_romData.data(), g_romData.size(), info)) {
                if (info.version == "PAL") chosenYaml = &palYaml;
            }

            // Generate OTR
            std::vector<uint8_t> otr;
            if (!otrGen.generateOTR(g_romData.data(), g_romData.size(),
                                    reinterpret_cast<const char*>(chosenYaml->data()), chosenYaml->size(),
                                    otr)) {
                LOGE("OTR generation failed");
            } else {
                g_otrData = std::move(otr);

                // Save cache
                mkdir("/data/data/com.bkawrapper/files", 0755);
                std::ofstream out("/data/data/com.bkawrapper/files/otr_cache.bin", std::ios::binary);
                if(out) out.write(reinterpret_cast<char*>(g_otrData.data()), g_otrData.size());
                out.close();

                LOGI("OTR generation complete, size: %zu bytes", g_otrData.size());
            }

        } catch (const std::exception& e) {
            LOGE("Exception in OTR generation: %s", e.what());
        } catch (...) {
            LOGE("Unknown error in OTR generation");
        }

        g_building = false;

    }, mgr).detach();
}

// ------------------------------
// JNI: get progress
// ------------------------------
extern "C" JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getOTRProgress(JNIEnv*, jclass) {
    return g_progress;
}

// ------------------------------
// JNI: get generated OTR bytes
// ------------------------------
extern "C" JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getOTR(JNIEnv* env, jclass) {
    jbyteArray arr = env->NewByteArray(g_otrData.size());
    if (arr) env->SetByteArrayRegion(arr, 0, g_otrData.size(), reinterpret_cast<jbyte*>(g_otrData.data()));
    return arr;
}