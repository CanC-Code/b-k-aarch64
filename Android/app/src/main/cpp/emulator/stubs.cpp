#include <cstdint>
#include <cstring>
#include <android/log.h>

#define LOG_TAG "BK_STUBS"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

static bool g_logged_reset = false;
static bool g_logged_audio = false;

// ------------------------------------------------------------
// SAFE TEMPORARY CORE STUBS
// ------------------------------------------------------------
extern "C" {

// ------------------------------------------------------------
// Core 1 (CPU)
// ------------------------------------------------------------
void core1_reset(uint8_t* ram) {
    if (!ram) return;

    if (!g_logged_reset) {
        LOGI("core1_reset (stub)");
        g_logged_reset = true;
    }

    // Clear first 64 KB only (fast + safe)
    memset(ram, 0, 64 * 1024);
}

void core1_stepCPU(uint8_t* /* ram */) {
    // Intentionally empty
}

// ------------------------------------------------------------
// Core 2 (Video)
// ------------------------------------------------------------
void core2_stepFrame(
        uint8_t* /* ram */,
        uint32_t* framebuffer,
        int width,
        int height) {

    if (!framebuffer || width <= 0 || height <= 0) return;

    // Simple moving color bars so you KNOW rendering works
    static uint32_t frame = 0;
    frame++;

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            uint8_t r = (x + frame) & 0xFF;
            uint8_t g = (y + frame) & 0xFF;
            uint8_t b = frame & 0xFF;

            framebuffer[y * width + x] =
                    0xFF000000 |
                    (r << 16) |
                    (g << 8) |
                    b;
        }
    }
}

// ------------------------------------------------------------
// Audio
// ------------------------------------------------------------
void n_audioInit() {
    if (!g_logged_audio) {
        LOGI("audio init (stub)");
        g_logged_audio = true;
    }
}

void n_audioStep() {
    // Silent stub
}

// ------------------------------------------------------------
// OTR loader
// ------------------------------------------------------------
// IMPLEMENTED IN ultra/otr_builder.cpp — do NOT define here
extern void core1_loadOTR(uint8_t* romData, size_t romSize);

} // extern "C"