// File: Android/app/src/main/cpp/ultra/stub_core.cpp
// Purpose: Temporary stubs for core/audio functions to allow Android build

#include <cstdint>
#include <cstddef>

extern "C" {

// ---- Core 1 ----
void core1_reset(uint8_t* ram) {
    // stub
}

void core1_stepCPU(uint8_t* ram) {
    // stub
}

// ---- Core 2 ----
void core2_stepFrame(uint8_t* ram, uint32_t* framebuffer, int width, int height) {
    // stub
}

// ---- Audio ----
void n_audioInit() {
    // stub
}

void n_audioStep() {
    // stub
}

void n_audioGetBuffer(int16_t* buffer, size_t samples) {
    if (!buffer) return;
    for (size_t i = 0; i < samples; i++) buffer[i] = 0; // silence
}

} // extern "C"