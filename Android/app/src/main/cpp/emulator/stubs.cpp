#include <android/log.h>
#include <stdint.h>
#include <stddef.h>

#define LOG_TAG "BKA_STUBS"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {

// ... keep existing stubs (core1_reset, etc) ...

void core1_loadOTR(uint8_t* data, size_t size) {
    if (!data) return;
    LOGI("core1_loadOTR: Loading OTR data into core (Size: %zu bytes)", size);
    // Real implementation would pass this buffer to the internal emulator engine
}

void core1_reset() {
    LOGI("core1_reset called");
}

void core1_stepCPU() {
    // CPU stepping logic
}

void core2_stepFrame() {
    // Frame stepping logic
}

} // extern "C"
