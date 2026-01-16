// File: asm/core1/ultra/android_setintmask.cpp
#include <cstdint>

#define CLR_SP 0x0001
#define SET_SP 0x0002
#define CLR_SI 0x0004
#define SET_SI 0x0008
#define CLR_AI 0x0010
#define SET_AI 0x0020
#define CLR_VI 0x0040
#define SET_VI 0x0080
#define CLR_PI 0x0100
#define SET_PI 0x0200
#define CLR_DP 0x0400
#define SET_DP 0x0800

// LUT exactly matching the original setintmask.s
constexpr uint16_t __osRcpImTable[64] = {
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
    SET_SP | SET_SI | SET_AI | SET_VI | SET_PI | SET_DP
};

extern "C" uint32_t __OSGlobalIntMask;
extern "C" volatile uint32_t* const MI_INTR_MASK_REG; // define properly in your environment

extern "C" void osSetIntMask(uint32_t mask) {
    uint32_t t4 = 0; // temporary CPU register simulation
    uint32_t t0, t1, t2, v0;

    // simulate MIPS mfc0 instruction
    t4 = 0; // read status register if needed

    v0 = t4 & 0xff01;
    t0 = __OSGlobalIntMask;
    t0 ^= 0xFFFFFFFF;
    t0 &= 0xff00;
    v0 |= t0;

    t2 = *MI_INTR_MASK_REG;
    if (t2 != 0) {
        t1 = (__OSGlobalIntMask >> 16) ^ 0xFFFFFFFF;
        t1 &= 0x3f;
        t2 |= t1;
    }
    v0 |= (t2 << 16);

    t0 = mask & 0x3f;
    t0 &= __OSGlobalIntMask;
    t0 >>= 15;
    t2 = __osRcpImTable[t0];
    *MI_INTR_MASK_REG = t2;

    t0 = mask & 0xff01;
    t1 = __OSGlobalIntMask & 0xff00;
    t0 &= t1;
    t4 &= 0xffff00ff;
    t4 |= t0;

    // simulate mtc0
    __OSGlobalIntMask = t4;
}