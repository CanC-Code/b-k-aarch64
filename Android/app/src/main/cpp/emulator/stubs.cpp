// File: Android/app/src/main/cpp/emulator/stubs.cpp
#include <cstdint>
#include <cstddef>
#include <android/log.h>

#define LOG_TAG "BKA_STUB"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {

// ---- CPU / Frame ----
void core1_stepCPU(uint8_t* ram) {
    LOGI("core1_stepCPU stub called");
}

void core2_stepFrame(uint8_t* ram, uint32_t* framebuffer, int width, int height) {
    LOGI("core2_stepFrame stub called");
    if (!framebuffer) return;
    // Simple checkerboard pattern
    for (int y = 0; y < height; y++)
        for (int x = 0; x < width; x++)
            framebuffer[y*width + x] = ((x/16 + y/16) % 2) ? 0xFF0000FF : 0xFFFF00FF;
}

// ---- Audio ----
void n_audioStep() {
    LOGI("n_audioStep stub called");
}

void n_audioGetBuffer(int16_t* buffer, size_t samples) {
    LOGI("n_audioGetBuffer stub called");
    if (!buffer) return;
    for (size_t i = 0; i < samples; ++i) buffer[i] = 0; // silence
}

void n_audioInit() {
    LOGI("n_audioInit stub called");
}

// ---- Reset ----
void core1_reset(uint8_t* ram) {
    LOGI("core1_reset stub called");
}

}