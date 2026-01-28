// File: app/src/main/cpp/ultra/exceptasm.cpp
#include <cstdint>
#include <cstring>

extern "C" {

// -----------------------------
// CPU / Exception state simulation
// -----------------------------
// Updated to match the N64 OSThread offset layout more closely for OTR compatibility
struct CPUState {
    /* 0x00 */ uint64_t at, v0, v1;
    /* 0x18 */ uint64_t a0, a1, a2, a3;
    /* 0x38 */ uint64_t t0, t1, t2, t3, t4, t5, t6, t7;
    /* 0x78 */ uint64_t s0, s1, s2, s3, s4, s5, s6, s7;
    /* 0xB8 */ uint64_t t8, t9;
    /* 0xC8 */ uint64_t gp, sp, fp, ra;
    /* 0xE8 */ uint64_t lo, hi; // Added HI/LO registers from .s file
    /* 0xF8 */ uint32_t status, cause, pc, badvaddr, rcp;
    /* 0x10C */ uint32_t fpcsr;
    /* 0x110 */ uint64_t fregs[32]; 
};

// OTR engines usually need these specific symbol names to handle scheduling
typedef struct OSThread_s {
    struct OSThread_s *next;
    int32_t priority;
    struct OSThread_s **queue;
    struct OSThread_s *tnext;
    CPUState context;
} OSThread;

OSThread* __osRunningThread = nullptr;
OSThread* __osRunQueue = nullptr;
OSThread* __osFaultedThread = nullptr;
CPUState __osThreadSave;

// -----------------------------
// Global interrupt state
// -----------------------------
volatile uint32_t __OSGlobalIntMask = 0xFFFFFFFF;
alignas(32) uintptr_t __osHwIntTable[5] = {0}; 
alignas(32) uint8_t   __osIntOffTable[32] = {0};
alignas(32) uintptr_t __osIntTable[9] = {0};

// -----------------------------
// Thread Management (The "Glue" for OTR)
// -----------------------------

// Port of the __osEnqueueThread logic from your .s file
void __osEnqueueThread(OSThread** queue, OSThread* thread) {
    OSThread* prev = (OSThread*)queue;
    OSThread* curr = *queue;

    while (curr != nullptr && curr->priority >= thread->priority) {
        prev = curr;
        curr = curr->next;
    }
    thread->next = curr;
    prev->next = thread;
}

OSThread* __osPopThread(OSThread** queue) {
    OSThread* thread = *queue;
    if (thread != nullptr) {
        *queue = thread->next;
    }
    return thread;
}

void __osDispatchThread() {
    __osRunningThread = __osPopThread(&__osRunQueue);
    // In a port, we don't 'eret', we just return to the main loop 
    // and the engine handles the next task.
}

// -----------------------------
// Interrupt handlers
// -----------------------------

void redispatch() {
    if (__osRunningThread) {
        __osEnqueueThread(&__osRunQueue, __osRunningThread);
    }
    __osDispatchThread();
}

void handleRCP() {
    // This is the most important for OTR. 
    // Signal the OTR Resource Manager that a Frame/Task is complete.
    redispatch(); 
}

void handleCart() {
    if (__osHwIntTable[4]) {
        ((void (*)())__osHwIntTable[4])();
    }
    redispatch();
}

// -----------------------------
// Initialization
// -----------------------------

void initInterruptTables() {
    // Fill the offsets based on your .s rdata section
    static const uint8_t defaultOffsets[32] = {
        0, 20, 24, 24, 28, 28, 28, 28, 32, 32, 24, 24, 28, 28, 28, 28,
        0, 4, 8, 8, 12, 12, 12, 12, 16, 16, 16, 16, 16, 16, 16, 16
    };
    std::memcpy((void*)__osIntOffTable, defaultOffsets, 32);
}

} // extern "C"
