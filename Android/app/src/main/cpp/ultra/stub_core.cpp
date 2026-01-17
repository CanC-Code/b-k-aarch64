// Purpose: Temporary stubs for core1/core2/audio functions to allow Android build
// Author: CCVO

#include <cstdint>
#include <cstddef>

extern "C" {

// ---- Core 1 ----
void core1_reset(uint8_t* ram) {
    // Stub: do nothing
}

void core1_stepCPU(uint8_t* ram) {
    // Stub: do nothing
}

// ---- Core 2 ----
void core2_stepFrame(uint8_t* ram, uint32_t* framebuffer, int width, int height) {
    // Stub: do nothing
}

// ---- Audio ----
void n_audioInit() {
    // Stub: do nothing
}

void n_audioStep() {
    // 