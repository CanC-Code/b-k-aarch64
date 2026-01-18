#include <jni.h>
#include <vector>
#include <cstdint>
#include <cstring>
#include <android/log.h>

#include "otr_builder.h"

#define LOG_TAG "BK_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Global buffers
static std::vector<uint8_t> g_rom;
static std::vector<uint8_t> g_otr;
static float g_progress = 0.0f;  // 0.0 -> 1.0

extern "C" {

// Load ROM bytes into memory
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRom(JNIEnv* env, jclass, jbyteArray romData) {
    if (!romData) return;
    const jsize romSize = env->GetArrayLength(romData);
    g_rom.resize(romSize);
    env->GetByteArrayRegion(romData, 0, romSize, reinterpret_cast<jbyte*>(g_rom.data()));
    LOGI("ROM loaded: %d bytes", romSize);
}

// Generate OTR
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processRom(JNIEnv* env, jclass) {
    g_otr.clear();
    g_progress = 0.0f;

    // Simulate progress callback
    auto progressCallback = [](float p) {
        g_progress = p;
    };

    bool success = buildBKOTR(
        g_rom.data(),
        g_rom.size(),
        nullptr, 0,           // Use null yaml for now if buildBKOTR supports it
        g_otr,
        progressCallback      // Pass callback
    );

    if (!success) LOGE("OTR build failed");
    else LOGI("OTR build complete: %zu bytes", g_otr.size());
}

// Return current progress (0.0 -> 1.0)
JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getOTRProgress(JNIEnv*, jclass) {
    return g_progress;
}

// Return OTR bytes
JNIEXPORT jbyteArray JNICALL
Java_com_bkawrapper_NativeBridge_getOTRData(JNIEnv* env, jclass) {
    if (g_otr.empty()) return nullptr;
    jbyteArray out = env->NewByteArray(g_otr.size());
    env->SetByteArrayRegion(out, 0, g_otr.size(), reinterpret_cast<const jbyte*>(g_otr.data()));
    return out;
}

// Save OTR to file
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_saveOTRToFile(JNIEnv* env, jclass, jstring path) {
    if (g_otr.empty()) return;
    const char* cpath = env->GetStringUTFChars(path, nullptr);
    FILE* f = fopen(cpath, "wb");
    if (f) {
        fwrite(g_otr.data(), 1, g_otr.size(), f);
        fclose(f);
    }
    env->ReleaseStringUTFChars(path, cpath);
}

} // extern "C"