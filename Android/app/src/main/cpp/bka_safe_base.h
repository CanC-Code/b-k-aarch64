#pragma once
/*
 * bka_safe_base.h  –  BKA Android N64 address translation layer
 *
 * THREAD SAFETY
 * ─────────────
 * gN64_RDRAM is written once during InitN64Registers() which MUST be
 * called from the JNI init path before BKA-GameThread is spawned.
 * BKA_Validate_And_Translate uses an atomic load with acquire semantics
 * as a secondary safety net, but the primary guarantee must come from
 * the caller ensuring InitN64Registers() has returned before any game
 * thread executes recompiled N64 code.
 *
 * RDRAM SIZE
 * ──────────
 * The physical N64 RDRAM is 8 MB (0x800000).  The decompiled code may
 * perform speculative over-reads up to address 0x800018 and beyond.
 * gN64_RDRAM must therefore be allocated as at least 16 MB (0x1000000).
 * Use BKA_RDRAM_ALLOC_SIZE for the malloc/mmap call in your JNI init.
 */

#include <android/log.h>
#include <stdint.h>

#define BKA_RDRAM_ALLOC_SIZE  (0x1000000u)   /* 16 MB – covers 0x800018 over-reads */
#define BKA_RDRAM_PHYS_SIZE   (0x800000u)    /* 8 MB  – original N64 RDRAM           */

#ifdef __cplusplus
extern "C" {
#endif

/*
 * These three globals are written ONCE by InitN64Registers() before any
 * game thread starts.  Reads from the game thread use acquire-load so
 * the processor cannot speculate past the initialisation write.
 */
extern uint8_t* gN64_RDRAM;
extern uint32_t* gN64_Reg_Base;
extern uint32_t* gN64_PIF_Base;

extern void InitN64Registers(const char* assetDir);

#ifdef __cplusplus
}
#endif

/* ── Address translation ──────────────────────────────────────────────── */

static inline uintptr_t BKA_Validate_And_Translate(
        uintptr_t addr, const char* file, int line)
{
    uintptr_t orig_addr = addr;
    uint32_t mask32 = (uint32_t)(addr & 0xFFFFFFFFu);
    addr &= 0x00FFFFFFFFFFFFFFULL;

    if (mask32 == 0u) return 0u;

    /* Pass through genuine 64-bit host pointers unchanged. */
    if ((orig_addr >> 32) != 0u && (orig_addr >> 32) != 0xFFFFFFFFu) return orig_addr;

    /*
     * Acquire-load: if gN64_RDRAM was written by InitN64Registers() on
     * another thread, this load is guaranteed to observe the write.
     * We utilize compiler built-ins here to strictly avoid standard 
     * library <stdatomic.h> imports, which pull in C++ templates that 
     * inherently crash inside legacy extern "C" headers.
     */
    uint8_t* ram_ptr = __atomic_load_n(&gN64_RDRAM,    __ATOMIC_ACQUIRE);
    uint32_t* reg_ptr = __atomic_load_n(&gN64_Reg_Base, __ATOMIC_ACQUIRE);
    uint32_t* pif_ptr = __atomic_load_n(&gN64_PIF_Base, __ATOMIC_ACQUIRE);

    if (!ram_ptr) {
        __android_log_print(ANDROID_LOG_FATAL, "BKA_MEM_FAULT",
            "[%s:%d] BKA_TRANSLATE_ADDR called before InitN64Registers(). "
            "addr=0x%08x", file, line, mask32);
        return addr;
    }

    uintptr_t ram = (uintptr_t)ram_ptr;
    uintptr_t reg = (uintptr_t)reg_ptr;
    uintptr_t pif = (uintptr_t)pif_ptr;

    /* RDRAM – bare physical (0x000000 – 0x0FFFFF) and over-read window */
    if (mask32 < BKA_RDRAM_ALLOC_SIZE)            return ram + mask32;
    /* RDRAM – K0 cached segment  (0x80000000) */
    if (mask32 >= 0x80000000u && mask32 < 0x81000000u)
                                                   return ram + (mask32 - 0x80000000u);
    /* RDRAM – K1 uncached segment (0xA0000000) */
    if (mask32 >= 0xA0000000u && mask32 < 0xA1000000u)
                                                   return ram + (mask32 - 0xA0000000u);
    /* RSP DMEM/IMEM / RCP registers (0x04000000) */
    if (mask32 >= 0x04000000u && mask32 < 0x05000000u)
                                                   return reg + (mask32 - 0x04000000u);
    if (mask32 >= 0xA4000000u && mask32 < 0xA5000000u)
                                                   return reg + (mask32 - 0xA4000000u);
    /* RSP DMEM/IMEM uncached mirror (0x40000000) */
    if (mask32 >= 0x40000000u && mask32 < 0x41000000u)
                                                   return reg + (mask32 - 0x40000000u);
                                                   return reg + (mask32 - 0xA4000000u);
    /* PIF ROM/RAM (0x1FC00000) */
    if (mask32 >= 0x1FC00000u && mask32 < 0x1FC01000u)
                                                   return pif + (mask32 - 0x1FC00000u);
    if (mask32 >= 0xBFC00000u && mask32 < 0xBFC01000u)
                                                   return pif + (mask32 - 0xBFC00000u);

    __android_log_print(ANDROID_LOG_FATAL, "BKA_MEM_FAULT",
        "[%s:%d] UNMAPPED N64 ACCESS: 0x%08x", file, line, mask32);
    return addr;  /* let the real fault happen so tombstone is useful */
}

#define BKA_TRANSLATE_ADDR(addr)     BKA_Validate_And_Translate((uintptr_t)(addr), __FILE__, __LINE__)

static inline uint32_t BKA_Reverse_Addr(uintptr_t addr)
{
    uint8_t* ram_ptr = __atomic_load_n(&gN64_RDRAM,    __ATOMIC_ACQUIRE);
    uint32_t* reg_ptr = __atomic_load_n(&gN64_Reg_Base, __ATOMIC_ACQUIRE);
    if (!ram_ptr) return (uint32_t)addr;
    uintptr_t ram = (uintptr_t)ram_ptr;
    uintptr_t reg = (uintptr_t)reg_ptr;
    if (addr >= ram && addr < ram + BKA_RDRAM_ALLOC_SIZE) return (uint32_t)(addr - ram);
    if (addr >= reg && addr < reg + 0x01000000u) return (uint32_t)((addr - reg) + 0x04000000u);
    return (uint32_t)addr;
}


/* ── HLE Stubs (Interceptor) ─────────────────────────────────────────── */
#ifdef __cplusplus
extern "C" {
#endif

void __original___osInitialize_common(void) {
    // Stubbed: Prevents N64 hardware crash
}

void __original___osViInit(void) {
    // Stubbed: Prevents VI crash
}

#ifdef __cplusplus
}
#endif
