#include <cstdint>
#include <android/log.h>
#include <unistd.h>

#define LOG_TAG "BK_STUBS"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

/*
 * These are TEMPORARY SAFE IMPLEMENTATIONS.
 * They keep the process alive and prevent crashes.
 * Real implementations will replace these later.
 */

extern "C" {

void core1_reset(uint8_t* ram) {
    LOGI("core1_reset called (stub)");
}

void core1_stepCPU() {
    // Stub: do nothing safely
}

void core2_stepFrame() {
    // Stub: do nothing safely
}

void n_audioInit() {
    LOGI("audio init (stub)");
}

void n_audioStep() {
    // Stub: do nothing safely
}

void core1_loadOTR(const char* path) {
    LOGI("load OTR: %s (stub)", path ? path : "<null>");
}

}