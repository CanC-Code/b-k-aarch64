// File: app/src/main/cpp/ultra/exceptasm.cpp
#include <cstdint>
#include <cstring>

extern "C" {

// -----------------------------
// CPU/Exception state simulation
// -----------------------------
struct CPUState {
    uint64_t at, v0, v1;
    uint64_t a0, a1, a2, a3;
    uint64_t t0, t1, t2, t3, t4, t5, t6, t7, t8, t9;
    uint64_t s0, s1, s2, s3, s4, s5, s6, s7;
    uint64_t gp, sp, fp, ra;
    uint64_t fregs[32]; // FPU
    uint32_t status, cause, epc, badvaddr;
};

CPUState __osThreadSave;
CPUState* __osRunningThread = nullptr;

// Global interrupt mask
volatile uint32_t __OSGlobalIntMask = 0;

// Simulated interrupt tables
alignas(32) volatile uint32_t __osHwIntTable[8] = {0};
alignas(32) volatile uint8_t  __osIntOffTable[32] = {0};
alignas(32) volatile uint32_t __osIntTable[32] = {0};

// -----------------------------
// Helper functions
// -----------------------------
inline void writeReg32(volatile uint32_t* addr, uint32_t value) { *addr = value; }
inline uint32_t readReg32(volatile uint32_t* addr) { return *addr; }

void saveExceptionState(CPUState* thread, const CPUState* current) {
    if (!thread || !current) return;
    std::memcpy(thread, current, sizeof(CPUState));
}

void restoreRunningThread() {
    if (!__osRunningThread) return;
    saveExceptionState(__osRunningThread, &__osThreadSave);
}

// -----------------------------
// Interrupt handlers (simulation)
// -----------------------------
void redispatch() { restoreRunningThread(); }

void handleCounter() { __osThreadSave.t0++; redispatch(); }
void handleCart() { 
    if (__osHwIntTable[4]) {
        void (*handler)() = reinterpret_cast<void(*)()>(__osHwIntTable[4]);
        handler();
    }
    redispatch();
}
void handleRCP() { redispatch(); }
void handleSW1() { redispatch(); }
void handleSW2() { redispatch(); }
void handlePRENMI() { __osThreadSave.status &= ~0x1001; redispatch(); }
void handleIP6() { __osThreadSave.status &= ~0x2001; redispatch(); }
void handleIP7() { __osThreadSave.status &= ~0x4001; redispatch(); }

// -----------------------------
// Exception dispatcher
// -----------------------------
void exceptionDispatcher(uint32_t cause) {
    switch (cause) {
        case 0x00: redispatch(); break;
        case 0x04: handleSW1(); break;
        case 0x08: handleSW2(); break;
        case 0x0C: handleRCP(); break;
        case 0x10: handleCart(); break;
        case 0x14: handlePRENMI(); break;
        case 0x18: handleIP6(); break;
        case 0x1C: handleIP7(); break;
        case 0x20: handleCounter(); break;
        default: redispatch(); break;
    }
}

// -----------------------------
// Initialize simulated interrupt tables
// -----------------------------
void initInterruptTables() {
    for (int i = 0; i < 32; i++) {
        __osIntOffTable[i] = i % 8;  
        __osIntTable[i] = reinterpret_cast<uint32_t>(&redispatch);
    }
}

} // extern "C"