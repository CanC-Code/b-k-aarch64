// File: android_setintmask.cpp
// Purpose: Native replacement for MIPS osSetIntMask assembly, adapted for Android
#include <cstdint>
#include <array>

// ---------- Definitions ----------
constexpr uint16_t CLR_SP = 0x0001;
constexpr uint16_t SET_SP = 0x0002;
constexpr uint16_t CLR_SI = 0x0004;
constexpr uint16_t SET_SI = 0x0008;
constexpr uint16_t CLR_AI = 0x0010;
constexpr uint16_t SET_AI = 0x0020;
constexpr uint16_t CLR_VI = 0x0040;
constexpr uint16_t SET_VI = 0x0080;
constexpr uint16_t CLR_PI = 0x0100;
constexpr uint16_t SET_PI = 0x0200;
constexpr uint16_t CLR_DP = 0x0400;
constexpr uint16_t SET_DP = 0x0800;

// ---------- LUT for MI_INTR -> MI_INTR_MASK ----------
alignas(4) static const std::array<uint16_t, 64> osRcpImTable = {
    CLR_SP | CLR_SI | CLR_AI | CLR_VI | CLR_PI | CLR_DP,
    SET_SP | CLR_SI | CLR_AI | CLR_VI | CLR_PI | CLR_DP,
    CLR_SP | SET_SI | CLR_AI | CLR_VI | CLR_PI | CLR_DP,
    SET_SP | SET_SI | CLR_AI | CLR_VI | CLR_PI | CLR_DP,
    CLR_SP | CLR_SI | SET_AI | CLR_VI | CLR_PI | CLR_DP,
    SET_SP | CLR_SI | SET_AI | CLR_VI | CLR_PI | CLR_DP,
    CLR_SP | SET_SI | SET_AI | CLR_VI | CLR_PI | CLR_DP,
    SET_SP | SET_SI | SET_AI | CLR_VI | CLR_PI | CLR_DP,
    CLR_SP | CLR_SI | CLR_AI | SET_VI | CLR_PI | CLR_DP,
    SET_SP | CLR_SI | CLR_AI | SET_VI | CLR_PI | CLR_DP,
    CLR_SP | SET_SI | CLR_AI | SET_VI | CLR_PI | CLR_DP,
    SET_SP | SET_SI | CLR_AI | SET_VI | CLR_PI | CLR_DP,
    CLR_SP | CLR_SI | SET_AI | SET_VI | CLR_PI | CLR_DP,
    SET_SP | CLR_SI | SET_AI | SET_VI | CLR_PI | CLR_DP,
    CLR_SP | SET_SI | SET_AI | SET_VI | CLR_PI | CLR_DP,
    SET_SP | SET_SI | SET_AI | SET_VI | CLR_PI | CLR_DP,
    CLR_SP | CLR_SI | CLR_AI | CLR_VI | SET_PI | CLR_DP,
    SET_SP | CLR_SI | CLR_AI | CLR_VI | SET_PI | CLR_DP,
    CLR_SP | SET_SI | CLR_AI | CLR_VI | SET_PI | CLR_DP,
    SET_SP | SET_SI | CLR_AI | CLR_VI | SET_PI | CLR_DP,
    CLR_SP | CLR_SI | SET_AI | CLR_VI | SET_PI | CLR_DP,
    SET_SP | CLR_SI | SET_AI | CLR_VI | SET_PI | CLR_DP,
    CLR_SP | SET_SI | SET_AI | CLR_VI | SET_PI | CLR_DP,
    SET_SP | SET_SI | SET_AI | CLR_VI | SET_PI | CLR_DP,
    CLR_SP | CLR_SI | CLR_AI | SET_VI | SET_PI | CLR_DP,
    SET_SP | CLR_SI | CLR_AI | SET_VI | SET_PI | CLR_DP,
    CLR_SP | SET_SI | CLR_AI | SET_VI | SET_PI | CLR_DP,
    SET_SP | SET_SI | CLR_AI | SET_VI | SET_PI | CLR_DP,
    CLR_SP | CLR_SI | SET_AI | SET_VI | SET_PI | CLR_DP,
    SET_SP | CLR_SI | SET_AI | SET_VI | SET_PI | CLR_DP,
    CLR_SP | SET_SI | SET_AI | SET_VI | SET_PI | CLR_DP,
    SET_SP | SET_SI | SET_AI | SET_VI | SET_PI | CLR_DP,
    CLR_SP | CLR_SI | CLR_AI | CLR_VI | CLR_PI | SET_DP,
    SET_SP | CLR_SI | CLR_AI | CLR_VI | CLR_PI | SET_DP,
    CLR_SP | SET_SI | CLR_AI | CLR_VI | CLR_PI | SET_DP,
    SET_SP | SET_SI | CLR_AI | CLR_VI | CLR_PI | SET_DP,
    CLR_SP | CLR_SI | SET_AI | CLR_VI | CLR_PI | SET_DP,
    SET_SP | CLR_SI | SET_AI | CLR_VI | CLR_PI | SET_DP,
    CLR_SP | SET_SI | SET_AI | CLR_VI | CLR_PI | SET_DP,
    SET_SP | SET_SI | SET_AI | CLR_VI | CLR_PI | SET_DP,
    CLR_SP | CLR_SI | CLR_AI | SET_VI | CLR_PI | SET_DP,
    SET_SP | CLR_SI | CLR_AI | SET_VI | CLR_PI | SET_DP,
    CLR_SP | SET_SI | CLR_AI | SET_VI | CLR_PI | SET_DP,
    SET_SP | SET_SI | CLR_AI | SET_VI | CLR_PI | SET_DP,
    CLR_SP | CLR_SI | SET_AI | SET_VI | CLR_PI | SET_DP,
    SET_SP | CLR_SI | SET_AI | SET_VI | CLR_PI | SET_DP,
    CLR_SP | SET_SI | SET_AI | SET_VI | CLR_PI | SET_DP,
    SET_SP | SET_SI | SET_AI | SET_VI | CLR_PI | SET_DP,
    CLR_SP | CLR_SI | CLR_AI | CLR_VI | SET_PI | SET_DP,
    SET_SP | CLR_SI | CLR_AI | CLR_VI | SET_PI | SET_DP,
    CLR_SP | SET_SI | CLR_AI | CLR_VI | SET_PI | SET_DP,
    SET_SP | SET_SI | CLR_AI | CLR_VI | SET_PI | SET_DP,
    CLR_SP | CLR_SI | SET_AI | CLR_VI | SET_PI | SET_DP,
    SET_SP | CLR_SI | SET_AI | CLR_VI | SET_PI | SET_DP,
    CLR_SP | SET_SI | SET_AI | CLR_VI | SET_PI | SET_DP,
    SET_SP | SET_SI | SET_AI | CLR_VI | SET_PI | SET_DP,
    CLR_SP | CLR_SI | CLR_AI | SET_VI | SET_PI | SET_DP,
    SET_SP | CLR_SI | CLR_AI | SET_VI | SET_PI | SET_DP,
    CLR_SP | SET_SI | CLR_AI | SET_VI | SET_PI | SET_DP,
    SET_SP | SET_SI | CLR_AI | SET_VI | SET_PI | SET_DP,
    CLR_SP | CLR_SI | SET_AI | SET_VI | SET_PI | SET_DP,
    SET_SP | CLR_SI | SET_AI | SET_VI | SET_PI | SET_DP,
    CLR_SP | SET_SI | SET_AI | SET_VI | SET_PI | SET_DP,
    SET_SP | SET_SI | SET_AI | SET_VI | SET_PI | SET_DP,
};

// ---------- Global Mask ----------
static uint16_t globalIntMask = 0;

// ---------- Replacement Function ----------
uint16_t osSetIntMask(uint16_t mask) {
    // Apply mask using LUT
    uint16_t tableIndex = mask & 0x3F; // only 6 bits for MI_INTR_MASK
    uint16_t imMask = osRcpImTable[tableIndex];

    // Combine with current mask
    uint16_t previous = globalIntMask;
    globalIntMask = (previous & 0xFF00) | (imMask & 0x00FF);

    return previous;
}