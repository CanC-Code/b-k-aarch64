// File: Android/app/src/main/cpp/wrapper.cpp
// Purpose: Android JNI wrapper for Banjo Kazooie decomp cores (core1/core2) with GPU-backed texture
// Author: CCVO
#include <jni.h>
#include <cstdint>
#include <vector>
#include <atomic>
#include <mutex>
#include <android/log.h>
#include <android/native_window_jni.h>
#include <android/native_window.h>
#include <GLES2/gl2.h>
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

// OpenGL texture
static GLuint gTexture = 0;

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
    if (!romData || romSize < 0x100) {
        LOGI("ROM too small or null");
        return;
    }

    // Copy 0x40-byte header
    BK_OTR.insert(BK_OTR.end(), romData, romData + 0x40);

    // 16 segments
    struct Segment { uint32_t start, end, dest; };
    Segment segments[16];

    for (int i = 0; i < 16; i++) {
        uint32_t start = (romData[0x40 + i*8 + 0] << 24) |
                         (romData[0x40 + i*8 + 1] << 16) |
                         (romData[0x40 + i*8 + 2] << 8)  |
                         (romData[0x40 + i*8 + 3]);
        uint32_t end   = (romData[0x40 + i*8 + 4] << 24) |
                         (romData[0x40 + i*8 + 5] << 16) |
                         (romData[0x40 + i*8 + 6] << 8)  |
                         (romData[0x40 + i*8 + 7]);

        if (start >= end || end > romSize) {
            segments[i] = {0,0,0};
            continue;
        }

        segments[i].start = start;
        segments[i].end   = end;
        segments[i].dest  = static_cast<uint32_t>(BK_OTR.size());

        // Copy segment
        BK_OTR.insert(BK_OTR.end(), romData + start, romData + end);
        LOGI("Segment %d: ROM 0x%08X->0x%08X => OTR 0x%08X (%u bytes)",
             i, start, end, segments[i].dest, end - start);
    }

    // Align OTR to 16-byte boundary
    size_t pad = (16 - (BK_OTR.size() % 16)) % 16;
    BK_OTR.insert(BK_OTR.end(), pad, 0);

    LOGI("Dynamic BK.OTR built: %zu bytes (+%zu padding)", BK_OTR.size(), pad);
}

// Accessor for cores
extern "C"
uint8_t* getOTRData(size_t* outSize) {
    if (outSize) *outSize = BK_OTR.size();
    return BK_OTR.empty() ? nullptr : BK_OTR.data();
}

// Optional: save OTR to disk
extern "C"
void saveOTRToFile(const char* path) {
    if (!path || BK_OTR.empty()) return;
    FILE* f = fopen(path, "wb");
    if (!f) return;
    fwrite(BK_OTR.data(), 1, BK_OTR.size(), f);
    fclose(f);
    LOGI("Saved BK.OTR: %zu bytes to %s", BK_OTR.size(), path);
}

// ---- OpenGL Texture Helpers ----
extern "C"
JNIEXPORT jint JNICALL
Java_com_bkawrapper_NativeBridge_initTexture(JNIEnv* env, jclass clazz) {
    glGenTextures(1, &gTexture);
    glBindTexture(GL_TEXTURE_2D, gTexture);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, gWidth, gHeight, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
    LOGI("OpenGL texture initialized: ID=%u", gTexture);
    return gTexture;
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_NativeBridge_updateTexture(JNIEnv* env, jclass clazz, jint texId) {
    std::lock_guard<std::mutex> lock(gFrameMutex);
    glBindTexture(GL_TEXTURE_2D, texId);
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, gWidth, gHeight,
                    GL_RGBA, GL_UNSIGNED_BYTE, gFrameBuffer);
}

// ---- JNI Exposed Functions ----
extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_loadRom(JNIEnv* env, jobject thiz, jbyteArray romData) {
    jsize len = env->GetArrayLength(romData);
    if (len > RAM_SIZE) len = RAM_SIZE;
    env->GetByteArrayRegion(romData, 0, len, reinterpret_cast<jbyte*>(n64RAM.data()));
    LOGI("ROM loaded: %d bytes into N64 RAM", len);
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_processRom(JNIEnv* env, jobject thiz) {
    core1_loadOTR(n64RAM.data(), n64RAM.size());
    LOGI("OTR processing complete");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_initGame(JNIEnv* env, jobject thiz, jobject surface) {
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
Java_com_bkawrapper_MainActivity_getFrameBuffer(JNIEnv* env, jobject thiz) {
    std::lock_guard<std::mutex> lock(gFrameMutex);
    jintArray out = env->NewIntArray(gWidth * gHeight);
    env->SetIntArrayRegion(out, 0, gWidth * gHeight, reinterpret_cast<jint*>(gFrameBuffer));
    return out;
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_stepFrame(JNIEnv* env, jobject thiz) {
    std::lock_guard<std::mutex> lock(gFrameMutex);
    core1_stepCPU(n64RAM.data());
    core2_stepFrame(n64RAM.data(), gFrameBuffer, gWidth, gHeight);
    n_audioStep();
}

extern "C"
JNIEXPORT jshortArray JNICALL
Java_com_bkawrapper_MainActivity_getAudioBuffer(JNIEnv* env, jobject thiz, jint samples) {
    jshortArray out = env->NewShortArray(samples);
    std::vector<int16_t> buffer(samples, 0);
    n_audioGetBuffer(buffer.data(), samples);
    env->SetShortArrayRegion(out, 0, samples, buffer.data());
    return out;
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_cleanupGame(JNIEnv* env, jobject thiz) {
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
Java_com_bkawrapper_MainActivity_saveOTR(JNIEnv* env, jobject thiz, jstring path) {
    const char* cpath = env->GetStringUTFChars(path, nullptr);
    saveOTRToFile(cpath);
    env->ReleaseStringUTFChars(path, cpath);
}

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    LOGI("BKA wrapper JNI_OnLoad called");
    return JNI_VERSION_1_6;
}