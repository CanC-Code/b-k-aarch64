// File: Android/app/src/main/cpp/setintmask.cpp
#include <cstdint>
#include <array>
#include "native_bridge.h" // For PHYS_TO_K1(MI_INTR_MASK_REG) etc.

// ---- Interrupt mask constants ----
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

constexpr uint16_t MI_INTR_MASK = 0x3F;

// ---- LUT matching __osRcpImTable in assembly ----
static constexpr std::array<uint16_t, 64> osRcpImTable = {
    CLR_SP|CLR_SI|CLR_AI|CLR_VI|CLR_PI|CLR_DP,
    SET_SP|CLR_SI|CLR_AI|CLR_VI|CLR_PI|CLR_DP,
    CLR_SP|SET_SI|CLR_AI|CLR_VI|CLR_PI|CLR_DP,
    SET_SP|SET_SI|CLR_AI|CLR_VI|CLR_PI|CLR_DP,
    CLR_SP|CLR_SI|SET_AI|CLR_VI|CLR_PI|CLR_DP,
    SET_SP|CLR_SI|SET_AI|CLR_VI|CLR_PI|CLR_DP,
    CLR_SP|SET_SI|SET_AI|CLR_VI|CLR_PI|CLR_DP,
    SET_SP|SET_SI|SET_AI|CLR_VI|CLR_PI|CLR_DP,
    CLR_SP|CLR_SI|CLR_AI|SET_VI|CLR_PI|CLR_DP,
    SET_SP|CLR_SI|CLR_AI|SET_VI|CLR_PI|CLR_DP,
    CLR_SP|SET_SI|CLR_AI|SET_VI|CLR_PI|CLR_DP,
    SET_SP|SET_SI|CLR_AI|SET_VI|CLR_PI|CLR_DP,
    CLR_SP|CLR_SI|SET_AI|SET_VI|CLR_PI|CLR_DP,
    SET_SP|CLR_SI|SET_AI|SET_VI|CLR_PI|CLR_DP,
    CLR_SP|SET_SI|SET_AI|SET_VI|CLR_PI|CLR_DP,
    SET_SP|SET_SI|SET_AI|SET_VI|CLR_PI|CLR_DP,
    CLR_SP|CLR_SI|CLR_AI|CLR_VI|SET_PI|CLR_DP,
    SET_SP|CLR_SI|CLR_AI|CLR_VI|SET_PI|CLR_DP,
    CLR_SP|SET_SI|CLR_AI|CLR_VI|SET_PI|CLR_DP,
    SET_SP|SET_SI|CLR_AI|CLR_VI|SET_PI|CLR_DP,
    CLR_SP|CLR_SI|SET_AI|CLR_VI|SET_PI|CLR_DP,
    SET_SP|CLR_SI|SET_AI|CLR_VI|SET_PI|CLR_DP,
    CLR_SP|SET_SI|SET_AI|CLR_VI|SET_PI|CLR_DP,
    SET_SP|SET_SI|SET_AI|CLR_VI|SET_PI|CLR_DP,
    CLR_SP|CLR_SI|CLR_AI|SET_VI|SET_PI|CLR_DP,
    SET_SP|CLR_SI|CLR_AI|SET_VI|SET_PI|CLR_DP,
    CLR_SP|SET_SI|CLR_AI|SET_VI|SET_PI|CLR_DP,
    SET_SP|SET_SI|CLR_AI|SET_VI|SET_PI|CLR_DP,
    CLR_SP|CLR_SI|SET_AI|SET_VI|SET_PI|CLR_DP,
    SET_SP|CLR_SI|SET_AI|SET_VI|SET_PI|CLR_DP,
    CLR_SP|SET_SI|SET_AI|SET_VI|SET_PI|CLR_DP,
    SET_SP|SET_SI|SET_AI|SET_VI|SET_PI|CLR_DP,
    CLR_SP|CLR_SI|CLR_AI|CLR_VI|SET_PI|SET_DP,
    SET_SP|CLR_SI|CLR_AI|CLR_VI|SET_PI|SET_DP,
    CLR_SP|SET_SI|CLR_AI|CLR_VI|SET_PI|SET_DP,
    SET_SP|SET_SI|CLR_AI|CLR_VI|SET_PI|SET_DP,
    CLR_SP|CLR_SI|SET_AI|CLR_VI|SET_PI|SET_DP,
    SET_SP|CLR_SI|SET_AI|CLR_VI|SET_PI|SET_DP,
    CLR_SP|SET_SI|SET_AI|CLR_VI|SET_PI|SET_DP,
    SET_SP|SET_SI|SET_AI|CLR_VI|SET_PI|SET_DP,
    CLR_SP|CLR_SI|CLR_AI|SET_VI|CLR_PI|SET_DP,
    SET_SP|CLR_SI|CLR_AI|SET_VI|CLR_PI|SET_DP,
    CLR_SP|SET_SI|CLR_AI|SET_VI|CLR_PI|SET_DP,
    SET_SP|SET_SI|CLR_AI|SET_VI|CLR_PI|SET_DP,
    CLR_SP|CLR_SI|SET_AI|SET_VI|CLR_PI|SET_DP,
    SET_SP|CLR_SI|SET_AI|SET_VI|CLR_PI|SET_DP,
    CLR_SP|SET_SI|SET_AI|SET_VI|CLR_PI|SET_DP,
    SET_SP|SET_SI|SET_AI|SET_VI|CLR_PI|SET_DP,
    CLR_SP|CLR_SI|CLR_AI|CLR_VI|SET_PI|SET_DP,
    SET_SP|CLR_SI|CLR_AI|CLR_VI|SET_PI|SET_DP,
    CLR_SP|SET_SI|CLR_AI|CLR_VI|SET_PI|SET_DP,
    SET_SP|SET_SI|CLR_AI|CLR_VI|SET_PI|SET_DP,
    CLR_SP|CLR_SI|SET_AI|CLR_VI|SET_PI|SET_DP,
    SET_SP|CLR_SI|SET_AI|CLR_VI|SET_PI|SET_DP,
    CLR_SP|SET_SI|SET_AI|CLR_VI|SET_PI|SET_DP,
    SET_SP|SET_SI|SET_AI|CLR_VI|SET_PI|SET_DP,
    CLR_SP|CLR_SI|CLR_AI|SET_VI|SET_PI|SET_DP,
    SET_SP|CLR_SI|CLR_AI|SET_VI|SET_PI|SET_DP,
    CLR_SP|SET_SI|CLR_AI|SET_VI|SET_PI|SET_DP,
    SET_SP|SET_SI|CLR_AI|SET_VI|SET_PI|SET_DP,
    CLR_SP|CLR_SI|SET_AI|SET_VI|SET_PI|SET_DP,
    SET_SP|CLR_SI|SET_AI|SET_VI|SET_PI|SET_DP,
    CLR_SP|SET_SI|SET_AI|SET_VI|SET_PI|SET_DP,
    SET_SP|SET_SI|SET_AI|SET_VI|SET_PI|SET_DP
};

// ---- Emulated global registers ----
static uint16_t __OSGlobalIntMask = 0;
static uint16_t MI_INTR_MASK_REG_EMU = 0;

extern "C" uint32_t osSetIntMask(uint32_t mask)
{
    // --- emulate CP0 Status read ---
    uint32_t cp0_status = 0; // placeholder for previous status
    uint16_t oldMask = __OSGlobalIntMask;

    // --- Calculate new mask ---
    uint16_t masked = mask & MI_INTR_MASK;
    uint16_t xorMask = oldMask ^ 0xFFFF;
    masked &= xorMask; // emulate XOR & AND with old mask

    // --- LUT indexing matches srl/andi in assembly ---
    uint16_t tableIndex = (masked & 0x3F); // exact mask applied
    uint16_t lutVal = osRcpImTable[tableIndex];

    // --- Update memory-mapped MI_INTR_MASK_REG ---
    MI_INTR_MASK_REG_EMU = lutVal;

    // --- Preserve upper/lower status bits like MIPS ---
    uint16_t t0 = mask & 0xFF01;
    uint16_t t1 = oldMask & 0xFF00;
    uint16_t finalStatus = (cp0_status & 0xFFFF00FF) | (t0 & t1);

    __OSGlobalIntMask = mask; // update global mask
    cp0_status = finalStatus;

    return cp0_status; // return previous "CP0 status"
}