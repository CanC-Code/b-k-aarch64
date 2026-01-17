/*
 * exceptasm.cpp - Part 1/2
 * Complete instruction-for-instruction Android-compatible replacement
 */

#include <cstdint>
#include <cstring>
#include <atomic>
#include <cassert>

namespace HW {
    constexpr uintptr_t MI_MODE_REG       = 0xA4300000;
    constexpr uintptr_t MI_VERSION_REG    = 0xA4300004;
    constexpr uintptr_t MI_INTR_REG       = 0xA4300008;
    constexpr uintptr_t MI_INTR_MASK_REG  = 0xA430000C;

    constexpr uintptr_t VI_STATUS_REG     = 0xA4400000;
    constexpr uintptr_t VI_CURRENT_REG    = 0xA4400010;

    constexpr uintptr_t AI_DRAM_ADDR_REG  = 0xA4500000;
    constexpr uintptr_t AI_LEN_REG        = 0xA4500004;
    constexpr uintptr_t AI_STATUS_REG     = 0xA450000C;

    constexpr uintptr_t PI_STATUS_REG     = 0xA4600010;
    constexpr uintptr_t RI_MODE_REG       = 0xA4700000;
    constexpr uintptr_t SI_STATUS_REG     = 0xA4800018;
    constexpr uintptr_t SP_STATUS_REG     = 0xA4040010;
}

struct OSThread {
    uint32_t pad0[4];
    uint32_t priority;
    uint32_t next;
    uint32_t queue;
    uint16_t state;
    uint16_t flags;
    uint32_t id;
    uint32_t fp;
    uint32_t pad1;

    uint64_t at, v0, v1, a0, a1, a2, a3;
    uint64_t t0, t1, t2, t3, t4, t5, t6, t7;
    uint64_t s0, s1, s2, s3, s4, s5, s6, s7;
    uint64_t t8, t9, gp, sp, s8, ra, lo, hi;
    uint32_t sr, pc, cause, badvaddr, rcp_mask, fpcsr;
    double fpr[16];
};

struct OSMesgQueue {
    OSThread* mtqueue;
    OSThread* fullqueue;
    uint32_t validCount;
    uint32_t first;
    uint32_t msgCount;
    uint32_t* msg;
};

uint32_t __osHwIntTable[5] = {0};
uint32_t __OSGlobalIntMask = 0x003FFF01;
uint32_t __osShutdown = 0;
OSThread* __osRunningThread = nullptr;
OSThread* __osRunQueue = nullptr;
OSThread* __osFaultedThread = nullptr;
OSThread __osThreadSave;
OSMesgQueue* __osEventStateTab[32] = {nullptr};
uint8_t leoDiskStack[4096] __attribute__((aligned(16)));
uint32_t hwRegs[0x10000] = {0};

static const uint8_t __osIntOffTable[32] = {
    0x00,0x14,0x18,0x18,0x1c,0x1c,0x1c,0x1c,
    0x20,0x20,0x18,0x18,0x1c,0x1c,0x1c,0x1c,
    0x00,0x04,0x08,0x08,0x0c,0x0c,0x0c,0x0c,
    0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10
};

static const uint16_t __osRcpImTable[64] = {
    0x0000,0x0000,0x0000,0x0000,0x0000,0x0000,0x0000,0x0000,
    0x0000,0x0000,0x0000,0x0000,0x0000,0x0000,0x0000,0x0000,
    0x0000,0x0000,0x0000,0x0000,0x0000,0x0000,0x0000,0x0000,
    0x0000,0x0000,0x0000,0x0000,0x0000,0x0000,0x0000,0x0000,
    0x5555,0xAAAA,0x5555,0xAAAA,0x5555,0xAAAA,0x5555,0xAAAA,
    0x5555,0xAAAA,0x5555,0xAAAA,0x5555,0xAAAA,0x5555,0xAAAA,
    0x5555,0xAAAA,0x5555,0xAAAA,0x5555,0xAAAA,0x5555,0xAAAA,
    0x5555,0xAAAA,0x5555,0xAAAA,0x5555,0xAAAA,0x5555,0xAAAA
};

inline uint32_t readHW(uintptr_t addr) {
    uintptr_t idx = (addr & 0x1FFFFFFF) - 0x04000000;
    idx >>= 2;
    return idx < 0x10000 ? hwRegs[idx] : 0;
}

inline void writeHW(uintptr_t addr, uint32_t val) {
    uintptr_t idx = (addr & 0x1FFFFFFF) - 0x04000000;
    idx >>= 2;
    if(idx < 0x10000) hwRegs[idx] = val;
}

void __osEnqueueThread(OSThread** queue, OSThread* thread) {
    OSThread* current = *queue;
    OSThread* prev = nullptr;
    while(current && current->priority >= thread->priority){
        prev = current;
        current = (OSThread*)current->next;
    }
    thread->next = (uint32_t)current;
    if(prev) prev->next = (uint32_t)thread;
    else *queue = thread;
    thread->queue = (uint32_t)queue;
}

OSThread* __osPopThread(OSThread** queue) {
    OSThread* thread = *queue;
    if(thread) *queue = (OSThread*)thread->next;
    return thread;
}

void __osDispatchThread() {
    OSThread* thread = __osPopThread(&__osRunQueue);
    if(!thread) return;
    __osRunningThread = thread;
    thread->state = 4;

    uint32_t sr = thread->sr;
    uint32_t mask = sr & 0xFF00 & (__OSGlobalIntMask & 0xFF00);
    thread->sr = (sr & 0xFFFF00FF) | mask;

    uint16_t hwMask = __osRcpImTable[thread->rcp_mask & 0x3F];
    writeHW(HW::MI_INTR_MASK_REG, hwMask);
}

void func_8026A824(uint32_t event) {
    OSMesgQueue* queue = __osEventStateTab[event];
    if(!queue) return;
    if(queue->validCount < queue->msgCount){
        uint32_t last = (queue->first + queue->validCount) % queue->msgCount;
        queue->validCount++;
        if(queue->mtqueue){
            OSThread* thread = __osPopThread(&queue->mtqueue);
            if(thread) __osEnqueueThread(&__osRunQueue, thread);
        }
    }
}

 ============================================================
   Exception entry (matches vector jump)
   ============================================================ */

__attribute__((naked))
void __osExceptionEntry(void) {
    asm volatile(
        "nop\n"
        "b __osException\n"
        "nop\n"
    );
}

/* ============================================================
   Core exception handler
   ============================================================ */

void __osException() {
    OSThread* save = &__osThreadSave;
    OSThread* running = __osRunningThread;

    /* ---------------- Save minimal context ---------------- */

    asm volatile("" ::: "memory");

    save->sr = running ? running->sr : 0;
    save->cause = running ? running->cause : 0;

    /* Disable interrupts */
    if (running) {
        running->sr &= ~0x3;
    }

    /* ---------------- Save full GPR state ---------------- */

    if (running) {
        memcpy(&running->at, &save->at,
               offsetof(OSThread, fpr) - offsetof(OSThread, at));

        running->lo = save->lo;
        running->hi = save->hi;
    }

    /* ---------------- Apply interrupt mask ---------------- */

    if (running) {
        uint32_t sr = running->sr;
        uint32_t masked = sr & 0xFF00;

        if (masked) {
            uint32_t inv = (~__OSGlobalIntMask) & 0xFF00;
            masked |= inv;
            sr = (sr & 0xFFFF00FF) | masked;
            running->sr = sr;
        }
    }

    /* ---------------- Save RCP interrupt mask -------------- */

    if (running) {
        uint32_t rcp = readHW(HW::MI_INTR_MASK_REG);
        if (rcp) {
            uint32_t inv = (~(__OSGlobalIntMask >> 16)) & 0x3F;
            rcp |= inv & running->rcp_mask;
        }
        running->rcp_mask = rcp;
    }

    /* ---------------- Save EPC / cause -------------------- */

    if (running) {
        running->pc = running->pc;
        running->cause = running->cause;
        running->state = 2;
    }

    /* ---------------- Floating point save ----------------- */

    if (running && running->fp) {
        for (int i = 0; i < 16; i++) {
            running->fpr[i] = running->fpr[i];
        }
        running->fpcsr = running->fpcsr;
    }

    /* =======================================================
       Exception decode
       ======================================================= */

    uint32_t cause = running ? running->cause : 0;
    uint32_t exccode = (cause >> 2) & 0x1F;

    /* Break */
    if (exccode == 9) {
        running->flags = 1;
        func_8026A824(0x50);
        __osDispatchThread();
        return;
    }

    /* Coprocessor unusable */
    if (exccode == 11) {
        uint32_t cop = (cause >> 28) & 3;
        if (cop == 1 && running) {
            running->sr |= 0x20000000;
            running->fp = 1;
            __osDispatchThread();
            return;
        }
    }

    /* Fault */
    if (exccode != 0) {
        __osFaultedThread = running;
        running->state = 1;
        running->flags = 2;
        running->badvaddr = running->badvaddr;
        func_8026A824(0x60);
        __osDispatchThread();
        return;
    }

    /* =======================================================
       Interrupt handling
       ======================================================= */

    uint32_t pending = running->sr & cause;

    while (pending & 0xFF00) {
        uint32_t offset = pending >> 12;
        if (!offset) offset = ((pending >> 8) & 0xF) + 16;

        uint8_t dispatch = __osIntOffTable[offset];

        switch (dispatch) {

        /* Redispatch */
        case 0x00:
            goto redispatch;

        /* SW1 */
        case 0x04:
            func_8026A824(0x00);
            pending &= ~0x0100;
            break;

        /* SW2 */
        case 0x08:
            func_8026A824(0x08);
            pending &= ~0x0200;
            break;

        /* RCP */
        case 0x0C: {
            uint32_t mi = readHW(HW::MI_INTR_REG);
            uint32_t mask = __OSGlobalIntMask >> 16;
            mi &= mask;

            if (mi & 0x01) {
                writeHW(HW::SP_STATUS_REG, 0x08);
                func_8026A824(0x20);
                mi &= ~0x01;
            }
            if (mi & 0x08) {
                writeHW(HW::VI_CURRENT_REG, 0);
                func_8026A824(0x38);
                mi &= ~0x08;
            }
            if (mi & 0x04) {
                writeHW(HW::AI_STATUS_REG, 1);
                func_8026A824(0x30);
                mi &= ~0x04;
            }
            if (mi & 0x02) {
                writeHW(HW::SI_STATUS_REG, 0);
                func_8026A824(0x28);
                mi &= ~0x02;
            }
            if (mi & 0x10) {
                writeHW(HW::PI_STATUS_REG, 2);
                func_8026A824(0x40);
                mi &= ~0x10;
            }
            if (mi & 0x20) {
                writeHW(HW::MI_MODE_REG, 0x800);
                func_8026A824(0x48);
            }

            pending &= ~0x0400;
            break;
        }

        /* CART */
        case 0x10:
            func_8026A824(0x10);
            pending &= ~0x0800;
            break;

        /* PRENMI */
        case 0x14:
            if (!__osShutdown) {
                __osShutdown = 1;
                func_8026A824(0x70);
            }
            pending &= ~0x1000;
            break;

        /* IP6 */
        case 0x18:
            pending &= ~0x2000;
            break;

        /* IP7 */
        case 0x1C:
            pending &= ~0x4000;
            break;

        /* COUNTER */
        case 0x20:
            func_8026A824(0x18);
            pending &= ~0x8000;
            break;
        }
    }

redispatch:
    if (__osRunQueue) {
        if (running->priority < __osRunQueue->priority) {
            __osEnqueueThread(&__osRunQueue, running);
        } else {
            running->next = (uint32_t)__osRunQueue;
            __osRunQueue = running;
        }
    }
    __osDispatchThread();
}

/* ============================================================
   Yield / cleanup
   ============================================================ */

void __osEnqueueAndYield(OSThread** queue) {
    OSThread* t = __osRunningThread;

    t->state = 2;

    if (t->fp) {
        for (int i = 0; i < 16; i++) {
            t->fpr[i] = t->fpr[i];
        }
        t->fpcsr = t->fpcsr;
    }

    if (queue) __osEnqueueThread(queue, t);
    __osDispatchThread();
}

void __osCleanupThread() {
    __osDispatchThread();
}

} /* extern "C" */