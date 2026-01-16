// File: src/core1/ultra_native/libm_vals.cpp
// Converted from asm/core1/ultra/libm_vals.s for Android N64 port

#include <cstdint>

namespace ultra_native {

// Quiet NaN float with bit pattern 0x7F810000
constexpr uint32_t __libm_qnan_bits = 0x7F810000;

// Optionally provide as a float for direct use
inline float libm_qnan_f() {
    float value;
    std::memcpy(&value, &__libm_qnan_bits, sizeof(value));
    return value;
}

} // namespace ultra_native