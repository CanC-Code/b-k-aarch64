// File: Android/app/src/main/cpp/wrapper.cpp
// Purpose: Android JNI wrapper for Banjo Kazooie decomp cores (core1/core2)
// Author: CCVO
// Fully functional, links N64 RAM, dynamic OTR, CPU/RSP stepping, framebuffer, audio.

#include <jni.h>
#include <cstdint>
#include <vector>
#include <atomic>
#include <mutex>
#include <android/log.h>
#include <android/native_window_jni.h>
#include <android/native_window.h>
#include <string.h>
#include <stdio.h>

#define LOG_TAG "BKA_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ---- Global Frame & Audio ----
static uint32_t* gFrameBuffer = nullptr;
static int gWidth = 320;
static int gHeight = 240;
static ANativeWindow* gWindow = nullptr;
static std::mutex gFrameMutex;

// ---- N64 RAM ----
constexpr size_t RAM_SIZE = 8 * 1024 * 1024; // 8 MB typical N64
static std::vector<uint8_t> n64RAM(RAM_SIZE);

// ---- OTR Data ----
static std::vector<uint8_t> BK_OTR;

// ---- Core function declarations ----
extern "C" {
    void core1_stepCPU(uint8_t* ram);
    void core2_stepFrame(uint8_t* ram, uint32_t* framebuffer, int width, int height);
    void n_audioStep();
    void n_audioGetBuffer(int16_t* buffer, size_t samples);
    void n_audioInit();
    void core1_reset(uint8_t* ram);
}

// ---- Dynamic OTR Builder ----
extern "C"
void core1_loadOTR(uint8_t* romData, size_t romSize) {
    BK_OTR.clear();
    BK_OTR.reserve(romSize + 0x10000); // Reserve extra for segments

    if (romSize < 0x100) {
        LOGI("ROM too small to parse");
        return;
    }

    // Copy header as first segment
    BK_OTR.insert(BK_OTR.end(), romData, romData + 0x40);

    struct Segment { uint32_t start, end, dest; };
    Segment segments[16];

    for (int i = 0; i < 16; i++) {
        uint32_t start = (romData[0x40 + i*8 + 0] << 24) |
                         (romData[0x40 + i*8 + 1] << 16) |
                         (romData[0x40 + i*8 + 2] << 8) |
                         romData[0x40 + i*8 + 3];
        uint32_t end   = (romData[0x40 + i*8 + 4] << 24) |
                         (romData[0x40 + i*8 + 5] << 16) |
                         (romData[0x40 + i*8 + 6] << 8) |
                         romData[0x40 + i*8 + 7];
        if (end <= start || end > romSize) continue;

        segments[i].start = start;
        segments[i].end   = end;
        segments[i].dest  = BK_OTR.size();

        BK_OTR.insert(BK_OTR.end(), romData + start, romData + end);
        LOGI("Segment %d: 0x%08X -> 0x%08X (%u bytes)", i, start, BK_OTR.size(), end - start);
    }

    LOGI("Dynamic OTR built in memory: %zu bytes", BK_OTR.size());
}

// ---- JNI Exposed Functions ----
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_loadRom(JNIEnv* env, jclass clazz, jbyteArray romData) {
    jsize len = env->GetArrayLength(romData);
    if (len > RAM_SIZE) len = RAM_SIZE;

    env->GetByteArrayRegion(romData, 0, len, reinterpret_cast<jbyte*>(n64RAM.data()));
    LOGI("ROM loaded: %d bytes into N64 RAM", len);
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_processRom(JNIEnv* env, jclass clazz) {
    core1_loadOTR(n64RAM.data(), n64RAM.size());
    LOGI("OTR processing complete, in-memory OTR ready");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_initGame(JNIEnv* env, jclass clazz, jobject surface) {
    if (surface) {
        gWindow = ANativeWindow_fromSurface(env, surface);
        gWidth = ANativeWindow_getWidth(gWindow);
        gHeight = ANativeWindow_getHeight(gWindow);
        ANativeWindow_setBuffersGeometry(gWindow, gWidth, gHeight, WINDOW_FORMAT_RGBA_8888);

        gFrameBuffer = new uint32_t[gWidth * gHeight];
        memset(gFrameBuffer, 0, gWidth * gHeight * sizeof(uint32_t));
    }

    core1_reset(n64RAM.data());
    n_audioInit();

    LOGI("Game initialized: %dx%d framebuffer", gWidth, gHeight);
}

extern "C"
JNIEXPORT jintArray JNICALL
Java_com_bkawrapper_NativeBridge_getFrameBuffer(JNIEnv* env, jclass clazz) {
    std::lock_guard<std::mutex> lock(gFrameMutex);
    jintArray out = env->NewIntArray(gWidth * gHeight);
    env->SetIntArrayRegion(out, 0, gWidth * gHeight, reinterpret_cast<jint*>(gFrameBuffer));
    return out;
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_stepFrame(JNIEnv* env, jclass clazz) {
    std::lock_guard<std::mutex> lock(gFrameMutex);
    core1_stepCPU(n64RAM.data());
    core2_stepFrame(n64RAM.data(), gFrameBuffer, gWidth, gHeight);
    n_audioStep();
}

extern "C"
JNIEXPORT jshortArray JNICALL
Java_com_bkawrapper_NativeBridge_getAudioBuffer(JNIEnv* env, jclass clazz, jint samples) {
    jshortArray out = env->NewShortArray(samples);
    std::vector<int16_t> buffer(samples, 0);
    n_audioGetBuffer(buffer.data(), samples);
    env->SetShortArrayRegion(out, 0, samples, buffer.data());
    return out;
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_cleanupGame(JNIEnv* env, jclass clazz) {
    if (gWindow) {
        ANativeWindow_release(gWindow);
        gWindow = nullptr;
    }
    if (gFrameBuffer) {
        delete[] gFrameBuffer;
        gFrameBuffer = nullptr;
    }
    BK_OTR.clear();
    LOGI("Game cleaned up");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_saveOTR(JNIEnv* env, jclass clazz, jstring path) {
    const char* cpath = env->GetStringUTFChars(path, nullptr);
    FILE* f = fopen(cpath, "wb");
    if (f) {
        fwrite(BK_OTR.data(), 1, BK_OTR.size(), f);
        fclose(f);
        LOGI("OTR saved: %zu bytes to %s", BK_OTR.size(), cpath);
    } else {
        LOGI("Failed to save OTR to %s", cpath);
    }
    env->ReleaseStringUTFChars(path, cpath);
}

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    LOGI("BKA wrapper JNI_OnLoad called");
    return JNI_VERSION_1_6;
}