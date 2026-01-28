// File: asm/core1/ultra/android_parameters.cpp
#include <cstdint>

extern "C" {

// Use volatile to prevent compiler optimizing out accesses
volatile uint32_t* const leoBootID       = reinterpret_cast<volatile uint32_t*>(0x800001a0);
volatile uint32_t* const osTvType        = reinterpret_cast<volatile uint32_t*>(0x80000300);
volatile uint32_t* const osRomType       = reinterpret_cast<volatile uint32_t*>(0x80000304);
volatile uint32_t* const osRomBase       = reinterpret_cast<volatile uint32_t*>(0x80000308);
volatile uint32_t* const osResetType     = reinterpret_cast<volatile uint32_t*>(0x8000030c);
volatile uint32_t* const osCicId         = reinterpret_cast<volatile uint32_t*>(0x80000310);
volatile uint32_t* const osVersion       = reinterpret_cast<volatile uint32_t*>(0x80000314);
volatile uint32_t* const osMemSize       = reinterpret_cast<volatile uint32_t*>(0x80000318);
volatile uint32_t* const osAppNMIBuffer  = reinterpret_cast<volatile uint32_t*>(0x8000031c);

// Pad to match original .space 0x60
alignas(0x60) uint8_t __parameters_pad[0x60] = {0};

} // extern "C"