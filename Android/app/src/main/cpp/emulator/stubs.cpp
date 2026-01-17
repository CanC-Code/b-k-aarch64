// emulator/stubs.cpp
// Minimal stubs for core and audio functions
#include <cstdint>

extern "C" {

// Core 1
void core1_stepCPU() {}
void core1_reset() {}

// Core 2
void core2_stepFrame() {}

// Audio
void n_audioStep() {}
void n_audioGetBuffer() {}
void n_audioInit() {}

} // extern "C"