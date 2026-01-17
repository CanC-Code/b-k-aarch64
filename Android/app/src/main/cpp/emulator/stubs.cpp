// File: Android/app/src/main/cpp/stubs.cpp
#include <cstdint>
#include <cstddef>

extern "C" {

void core1_stepCPU(uint8_t* ram) {
    // Dummy: do nothing
}

void core2_stepFrame(uint8_t* ram, uint32_t* framebuffer, int width, int height) {
    // Dummy: fill framebuffer with checkerboard
    if (!framebuffer) return;
    for (int y = 0; y < height; y++)
        for (int x = 0; x < width; x++)
            framebuffer[y*width + x] = ((x/16 + y/16) % 2) ? 0xFF0000FF : 0xFFFF00FF;
}

void n_audioStep() {
    // Dummy: do nothing
}

void n_audioGetBuffer(int16_t* buffer, size_t samples) {
    if (!buffer) return;
    for (size_t i = 0; i < samples; i++) buffer[i] = 0; // silence
}

void n_audioInit() {}
void core1_reset(uint8_t* ram) {}

}