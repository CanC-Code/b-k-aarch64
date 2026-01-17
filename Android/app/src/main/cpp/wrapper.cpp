// File: Android/app/src/main/cpp/wrapper.cpp
// Purpose: Android JNI wrapper for Banjo Kazooie decomp cores (core1/core2) with GPU-backed texture
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
    void core1_loadOTR(uint8_t* romData, size_t romSize);
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