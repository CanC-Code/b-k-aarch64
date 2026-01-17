// File: Android/app/src/main/cpp/wrapper.cpp
// Purpose: Android JNI wrapper for Banjo-Kazooie decomp cores (core1/core2) with GPU-backed texture
// Author: CCVO

#include <jni.h>
#include <cstdint>
#include <vector>
#include <atomic>
#include <mutex>
#include <thread>
#include <chrono>
#include <memory>
#include <android/log.h>
#include <android/native_window_jni.h>
#include <android/native_window.h>
#include <GLES2/gl2.h>
#include <string.h>
#include <stdio.h>

#define LOG_TAG "BKA_WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ---- Global Frame & Audio ----
static std::unique_ptr<uint32_t[]> gFrameBuffer;
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

// ---- Audio Cache ----
static std::vector<int16_t> gAudioCache;

// ---- Core function declarations ----
extern "C" {
    void core1_stepCPU(uint8_t* ram);
    void core2_stepFrame(uint8_t* ram, uint32_t* framebuffer, int width, int height);
    void n_audioStep();
    void n_audioGetBuffer(int16_t* buffer, size_t samples);
    void n_audioInit();
    void core1_reset(uint8_t* ram);

    // OTR builder
    void core1_loadOTR(uint8_t* romData, size_t romSize);
    uint8_t* getOTRData(size_t* outSize);
    void saveOTRToFile(const char* path);
}

// ---- Threaded Game Loop ----
static std::atomic<bool> gRunning = false;
static std::thread gLoopThread;

static void gameLoop() {
    while (gRunning) {
        {
            std::lock_guard<std::mutex> lock(gFrameMutex);
            core1_stepCPU(n64RAM.data());
            if (gFrameBuffer) core2_stepFrame(n64RAM.data(), gFrameBuffer.get(), gWidth, gHeight);
            n_audioStep();
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(16)); // ~60 FPS
    }
}

// ---- Framebuffer Helpers ----
static void resizeFrameBuffer(int width, int height) {
    std::lock_guard<std::mutex> lock(gFrameMutex);
    gWidth = width;
    gHeight = height;
    gFrameBuffer = std::make_unique<uint32_t[]>(gWidth * gHeight);
    memset(gFrameBuffer.get(), 0, gWidth * gHeight * sizeof(uint32_t));
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
        int width = ANativeWindow_getWidth(gWindow);
        int height = ANativeWindow_getHeight(gWindow);
        ANativeWindow_setBuffersGeometry(gWindow, width, height, WINDOW_FORMAT_RGBA_8888);
        resizeFrameBuffer(width, height);
    }
    core1_reset(n64RAM.data());
    n_audioInit();
    LOGI("Game initialized: %dx%d framebuffer", gWidth, gHeight);
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_resetGame(JNIEnv* env, jobject thiz) {
    std::fill(n64RAM.begin(), n64RAM.end(), 0);
    core1_reset(n64RAM.data());
    LOGI("Game reset complete");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_startGameLoop(JNIEnv* env, jobject thiz) {
    if (gRunning) return;
    gRunning = true;
    gLoopThread = std::thread(gameLoop);
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_stopGameLoop(JNIEnv* env, jobject thiz) {
    gRunning = false;
    if (gLoopThread.joinable()) gLoopThread.join();
}

extern "C"
JNIEXPORT jintArray JNICALL
Java_com_bkawrapper_MainActivity_getFrameBuffer(JNIEnv* env, jobject thiz) {
    std::lock_guard<std::mutex> lock(gFrameMutex);
    jintArray out = env->NewIntArray(gWidth * gHeight);
    if (gFrameBuffer) env->SetIntArrayRegion(out, 0, gWidth * gHeight, reinterpret_cast<jint*>(gFrameBuffer.get()));
    return out;
}

extern "C"
JNIEXPORT jshortArray JNICALL
Java_com_bkawrapper_MainActivity_getAudioBuffer(JNIEnv* env, jobject thiz, jint samples) {
    gAudioCache.resize(samples);
    n_audioGetBuffer(gAudioCache.data(), samples);
    jshortArray out = env->NewShortArray(samples);
    env->SetShortArrayRegion(out, 0, samples, gAudioCache.data());
    return out;
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_cleanupGame(JNIEnv* env, jobject thiz) {
    gRunning = false;
    if (gLoopThread.joinable()) gLoopThread.join();

    if (gWindow) {
        ANativeWindow_release(gWindow);
        gWindow = nullptr;
    }
    gFrameBuffer.reset();
    BK_OTR.clear();
    gAudioCache.clear();
    LOGI("Game cleaned up");
}

extern "C"
JNIEXPORT void JNICALL
Java_com_bkawrapper_MainActivity_saveOTR(JNIEnv* env, jobject thiz, jstring path) {
    const char* cpath = env->GetStringUTFChars(path, nullptr);
    saveOTRToFile(cpath);
    env->ReleaseStringUTFChars(path, cpath);
}

// ---- JNI OpenGL Texture ----
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
    if (!gFrameBuffer || texId <= 0) return;
    std::lock_guard<std::mutex> lock(gFrameMutex);
    glBindTexture(GL_TEXTURE_2D, texId);
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, gWidth, gHeight, GL_RGBA, GL_UNSIGNED_BYTE, gFrameBuffer.get());
}

// ---- JNI Load ----
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    LOGI("BKA wrapper JNI_OnLoad called");
    return JNI_VERSION_1_6;
}