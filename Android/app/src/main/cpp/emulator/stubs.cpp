#include <cstdint>
#include <cstring>
#include <android/log.h>

#define LOG_TAG "BK_STUBS"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

static bool g_logged_reset = false;
static bool g_logged_audio = false;

extern "C" {

void core1_reset(uint8_t* ram) {
    if (!ram) return;
    if (!g_logged_reset) { LOGI("core1_reset (stub)"); g_logged_reset = true; }
    memset(ram, 0, 64 * 1024);
}

void core1_stepCPU(uint8_t* /*ram*/) {}
void core2_stepFrame(uint8_t*, uint32_t* framebuffer, int width, int height) {
    if (!framebuffer || width <= 0 || height <= 0) return;
    static uint32_t frame = 0; frame++;
    for (int y=0; y<height; y++) for (int x=0; x<width; x++) {
        framebuffer[y*width+x] = 0xFF000000 | ((x+frame)&0xFF)<<16 | ((y+frame)&0xFF)<<8 | (frame&0xFF);
    }
}

void n_audioInit() { if (!g_logged_audio) { LOGI("audio init"); g_logged_audio=true; } }
void n_audioStep() {}

extern void core1_loadOTR(uint8_t*, size_t);
} // extern "C"