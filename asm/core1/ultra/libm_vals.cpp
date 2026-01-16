// File: libm_vals.cpp
// Purpose: Android-native replacement for libm_vals.s

#include <cstdint>
#include <cstddef>
#include <cstring>
#include <array>
#include <type_traits>

extern "C" {

// Ensure 32-bit aligned float
alignas(4) const uint32_t __libm_qnan_f = 0x7F810000;

}