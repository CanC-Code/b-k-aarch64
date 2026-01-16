// File: src/core1/ultra_native/parameters.cpp
// Converted from asm/core1/ultra/parameters.s for Android N64 port

#include <cstdint>

namespace ultra_native {

constexpr uintptr_t leoBootID      = 0x800001a0;
constexpr uintptr_t osTvType       = 0x80000300;
constexpr uintptr_t osRomType      = 0x80000304;
constexpr uintptr_t osRomBase      = 0x80000308;
constexpr uintptr_t osResetType    = 0x8000030c;
constexpr uintptr_t osCicId        = 0x80000310;
constexpr uintptr_t osVersion      = 0x80000314;
constexpr uintptr_t osMemSize      = 0x80000318;
constexpr uintptr_t osAppNMIBuffer = 0x8000031c;

// Padding for alignment
alignas(4) uint8_t padding[0x60] = {};

} // namespace ultra_native