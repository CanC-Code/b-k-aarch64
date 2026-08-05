// File: Banjo-android-realignment/Android/app/src/main/cpp/emulator/stubs.cpp

#include "HardwareRegs.h"
#include <android/log.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <pthread.h>
#include "n64_os_types_cpp.h"
// os_vi stubs in n64_os_types_cpp.h
#include <unordered_map>
#include <mutex>
#include <deque>
#include <condition_variable>
#include <memory>
#include <thread>
#include "n64_os_types_cpp.h"
#include "bka_safe_base.h"
#include "rarezip_stub_cpp.h"
extern OSMesgQueue D_8027FBC8;
#include "gfx_interpreter.h"   // <-- ADDED: F3DEX display list → framebuffer rasterizer


// -------------------------------------------------------------------------
// HIGH-LEVEL EMULATION NATIVE STRUCTURES
// -------------------------------------------------------------------------
struct NativeThread {
    pthread_t thread;
    void (*entry)(void *);
    void *arg;
    OSId id;
    OSPri pri;
    uint64_t last_yield_us;
};

struct NativeQueue {
    std::deque<OSMesg> buffer;
    int capacity;
    std::mutex mtx;
    std::condition_variable cv_recv;
    std::condition_variable cv_send;
};

struct EventRoute {
    OSMesgQueue* mq;
    OSMesg msg;
};

// -------------------------------------------------------------------------
// REGISTRIES & SYNCHRONIZATION (THE GIL)
// -------------------------------------------------------------------------
static std::recursive_mutex s_n64_gil;

static std::unordered_map<OSThread*, std::shared_ptr<NativeThread>> s_threadRegistry;
static std::mutex s_threadMutex;

static std::unordered_map<OSMesgQueue*, std::shared_ptr<NativeQueue>> s_queueRegistry;
static std::mutex s_queueMutex;

static std::unordered_map<int, EventRoute> s_eventRegistry;
static std::mutex s_eventMutex;

// PI Manager Subsystem Tracking
static OSMesgQueue* s_hlePiCmdQueue = nullptr;
static pthread_t    s_hlePiMgrThread;

// -------------------------------------------------------------------------
// RESOURCE READINESS GATE
// -------------------------------------------------------------------------
static pthread_mutex_t s_resourceGateMutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  s_resourceGateCond  = PTHREAD_COND_INITIALIZER;
static volatile bool   s_resourceReady     = false;

// Decompression mutex (for thread-safe bkboot_inflate)
extern pthread_mutex_t g_inflateMutex;

// -------------------------------------------------------------------------
// PREEMPTIVE GIL YIELD HELPER (outside extern "C" to use C++ structs)
// -------------------------------------------------------------------------
static inline uint64_t get_time_us(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000ULL + (uint64_t)ts.tv_nsec / 1000ULL;
}

// Must be called while holding s_n64_gil
static void PreemptiveYield(NativeThread* nt) {
    uint64_t now = get_time_us();
    if (now - nt->last_yield_us < 500) {
        return;
    }
    nt->last_yield_us = now;

    s_n64_gil.unlock();
    usleep(50);
    s_n64_gil.lock();
}

extern "C" {
// Recompiled OS headers
// os_pi types in n64_os_types_cpp.h
// os_thread types in n64_os_types_cpp.h
// os_message types in n64_os_types_cpp.h
// sptask types in n64_os_types_cpp.h
// os_ai stubs
// os_eeprom stubs

/* Forward declarations for HLE message queue functions */
s32 osSendMesg(OSMesgQueue *mq, OSMesg msg, s32 flag);
s32 osJamMesg(OSMesgQueue *mq, OSMesg msg, s32 flag);
s32 osRecvMesg(OSMesgQueue *mq, OSMesg *msg, s32 flag);

#define LOG_TAG "BKA_STUBS"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,  LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN,  LOG_TAG, __VA_ARGS__)

/* ============================================================
   1. OS GLOBALS & LINKER WRAPPING
   ============================================================ */

static OSPiHandle sPiTablePool[2];
OSPiHandle* __osPiTable = sPiTablePool;

void* __osViNext = nullptr;
void* __osViCurr = nullptr;
OSDevMgr __osPiDevMgr;
u32 __osEventStateTab[16];

// Required libultra hardware globals
s32 osTvType    = 1;           // 1 = NTSC, 2 = PAL
s32 osRomType   = 0;           // 0 = Cartridge
s32 osVersion   = 0;
s32 osResetType = 0;
u32 osMemSize   = 0x00800000;  // 8MB Expansion Pak

// Linker Wrap: Intercepts original assembly __osInitialize_common
extern void __real___osInitialize_common(void);

void __wrap___osInitialize_common(void) {
    LOGI("BKA-HLE: __osInitialize_common intercepted via Linker Wrap.");
}

void __osViInit(void) {
    LOGI("BKA-HLE: __osViInit executed.");
}

// VI stubs with correct N64 types from os_vi.h
void osViSetMode(OSViMode *modep)                        { (void)modep; }
void osViSetSpecialFeatures(u32 func)                    { (void)func; }
void osViSwapBuffer(void *vaddr)                         { (void)vaddr; }
void osViSetEvent(OSMesgQueue *mq, OSMesg m, u32 count)  { (void)mq; (void)m; (void)count; }
void osCreateViManager(OSPri pri)                         { (void)pri; }

/* ============================================================
   2. RESOURCE READINESS GATE API
   ============================================================ */

void BKA_SignalResourcesReady(void) {
    pthread_mutex_lock(&s_resourceGateMutex);
    s_resourceReady = true;
    pthread_cond_broadcast(&s_resourceGateCond);
    pthread_mutex_unlock(&s_resourceGateMutex);
    LOGI("BKA-STUBS: Resource gate opened — engine boot unblocked.");
}

static void WaitForResourcesReady(void) {
    pthread_mutex_lock(&s_resourceGateMutex);
    while (!s_resourceReady) {
        pthread_cond_wait(&s_resourceGateCond, &s_resourceGateMutex);
    }
    pthread_mutex_unlock(&s_resourceGateMutex);
}

/* ============================================================
   3. HLE NATIVE THREADING WITH GIL
   ============================================================ */

void osCreateThread(OSThread *t, OSId id, void (*entry)(void *), void *arg, void *sp, OSPri p) {
    if (!t) return;
    std::lock_guard<std::mutex> lock(s_threadMutex);
    t->id       = id;
    t->priority = p;

    auto nt = std::make_shared<NativeThread>();
    nt->entry   = entry;
    nt->arg     = arg;
    nt->id      = id;
    nt->pri     = p;
    nt->thread  = 0;
    nt->last_yield_us = get_time_us();

    s_threadRegistry[t] = nt;
}

static void* NativeThreadWrapper(void* arg) {
    auto ntPtr = static_cast<std::shared_ptr<NativeThread>*>(arg);
    std::shared_ptr<NativeThread> nt = *ntPtr;
    delete ntPtr;

    LOGI("BKA-HLE: Native Thread ID %d starting execution.", nt->id);

    s_n64_gil.lock();
    if (nt->entry != nullptr) {
        nt->entry(nt->arg);
    }
    s_n64_gil.unlock();

    LOGI("BKA-HLE: Native Thread ID %d terminated cleanly.", nt->id);
    return nullptr;
}

void osStartThread(OSThread *t) {
    std::lock_guard<std::mutex> lock(s_threadMutex);
    if (t != nullptr && s_threadRegistry.find(t) != s_threadRegistry.end()) {
        auto nt = s_threadRegistry[t];
        auto arg = new std::shared_ptr<NativeThread>(nt);
        if (pthread_create(&nt->thread, nullptr, NativeThreadWrapper, arg) == 0) {
            pthread_detach(nt->thread);
        } else {
            delete arg;
            LOGE("BKA-HLE: FATAL - Failed to create POSIX thread for OSThread ID %d", t->id);
        }
    }
}

void osStopThread(OSThread *t) {
    LOGW("BKA-HLE: osStopThread intercepted.");
}

void osDestroyThread(OSThread *t) {
    std::lock_guard<std::mutex> lock(s_threadMutex);
    if (s_threadRegistry.find(t) != s_threadRegistry.end()) {
        s_threadRegistry.erase(t);
    }
}

void osYieldThread(void) {
    s_n64_gil.unlock();
    std::this_thread::yield();
    usleep(100);
    s_n64_gil.lock();
}

void osSetThreadPri(OSThread *t, OSPri pri) { if (t) t->priority = pri; }
OSPri osGetThreadPri(OSThread *t)           { return t ? t->priority : 0; }
void __osDequeueThread(OSThread **queue, OSThread *t) {}

/* ============================================================
   4. EVENT ROUTING & MESSAGE QUEUES
   ============================================================ */

static std::shared_ptr<NativeQueue> GetNativeQueue(OSMesgQueue* mq) {
    if (!mq) return nullptr;
    std::lock_guard<std::mutex> lock(s_queueMutex);
    auto it = s_queueRegistry.find(mq);
    if (it != s_queueRegistry.end()) {
        return it->second;
    }
    return nullptr;
}

void osCreateMesgQueue(OSMesgQueue *mq, OSMesg *msgBuf, s32 count) {
    if (!mq) return;
    mq->validCount = 0;
    mq->first      = 0;
    mq->msgCount   = count;
    mq->msg        = msgBuf;

    std::lock_guard<std::mutex> lock(s_queueMutex);
    auto nq = std::make_shared<NativeQueue>();
    nq->capacity = count;
    s_queueRegistry[mq] = nq;
}

void osSetEventMesg(OSEvent e, OSMesgQueue *mq, OSMesg msg) {
    std::lock_guard<std::mutex> lock(s_eventMutex);
    s_eventRegistry[(int)e] = {mq, msg};
    LOGI("BKA-HLE: Bound hardware event %d to queue", (int)e);
}

void HLE_TriggerN64Event(int event_id) {
    EventRoute route{nullptr, nullptr};
    bool found = false;
    {
        std::lock_guard<std::mutex> lock(s_eventMutex);
        auto it = s_eventRegistry.find(event_id);
        if (it != s_eventRegistry.end()) {
            route = it->second;
            found = true;
        }
    }

    if (found && route.mq != nullptr) {
        osSendMesg(route.mq, route.msg, OS_MESG_NOBLOCK);
    }
}

s32 osSendMesg(OSMesgQueue *mq, OSMesg msg, s32 flag) {
    std::shared_ptr<NativeQueue> nq = GetNativeQueue(mq);
    if (!nq) return -1;

    std::unique_lock<std::mutex> lock(nq->mtx);
    if (flag == OS_MESG_BLOCK) {
        while ((int)nq->buffer.size() >= nq->capacity) {
            s_n64_gil.unlock();
            nq->cv_send.wait(lock);
            lock.unlock();
            s_n64_gil.lock();
            lock.lock();
        }
    } else {
        // Always accept messages (Android HLE - capacity ignored)
    }

    nq->buffer.push_back(msg);
    mq->validCount = static_cast<s32>(nq->buffer.size());
    nq->cv_recv.notify_one();
    return 0;
}

s32 osJamMesg(OSMesgQueue *mq, OSMesg msg, s32 flag) {
    std::shared_ptr<NativeQueue> nq = GetNativeQueue(mq);
    if (!nq) return -1;

    std::unique_lock<std::mutex> lock(nq->mtx);
    if (flag == OS_MESG_BLOCK) {
        while ((int)nq->buffer.size() >= nq->capacity) {
            s_n64_gil.unlock();
            nq->cv_send.wait(lock);
            lock.unlock();
            s_n64_gil.lock();
            lock.lock();
        }
    } else {
        // Always accept messages (Android HLE - capacity ignored)
    }

    nq->buffer.push_front(msg);
    mq->validCount = static_cast<s32>(nq->buffer.size());
    nq->cv_recv.notify_one();
    return 0;
}

s32 osRecvMesg(OSMesgQueue *mq, OSMesg *msg, s32 flag) {
    std::shared_ptr<NativeQueue> nq = GetNativeQueue(mq);
    if (!nq) return -1;

    std::unique_lock<std::mutex> lock(nq->mtx);
    if (flag == OS_MESG_BLOCK) {
        while (nq->buffer.empty()) {
            s_n64_gil.unlock();
            nq->cv_recv.wait(lock);
            lock.unlock();
            s_n64_gil.lock();
            lock.lock();
        }
    } else {
        if (nq->buffer.empty()) return -1;
    }

    if (msg != nullptr) *msg = nq->buffer.front();
    nq->buffer.pop_front();
        static int recvCount = 0; if (++recvCount <= 10 || recvCount % 100 == 0) __android_log_print(ANDROID_LOG_INFO, "BKA-RDP", "osRecvMesg: message %d received", recvCount);
    mq->validCount = static_cast<s32>(nq->buffer.size());
    nq->cv_send.notify_one();
    return 0;
}

/* ============================================================
   5. HLE DMA REDIRECTION
   ============================================================ */

static void* HLE_PiManagerWorker(void* arg) {
    LOGI("BKA-HLE: Peripheral Interface (PI) Async Manager Thread Engaged.");
    s_n64_gil.lock();

    // Retrieve our own NativeThread record for periodic yielding
    std::shared_ptr<NativeThread> myNT = nullptr;
    {
        std::lock_guard<std::mutex> lock(s_threadMutex);
        for (auto& pair : s_threadRegistry) {
            if (pair.second->thread == pthread_self()) {
                myNT = pair.second;
                break;
            }
        }
    }

    while (true) {
        if (s_hlePiCmdQueue == nullptr) {
            if (myNT) PreemptiveYield(myNT.get());
            else {
                s_n64_gil.unlock();
                usleep(10000);
                s_n64_gil.lock();
            }
            continue;
        }

        OSMesg msg = nullptr;
        s32 ret = osRecvMesg(s_hlePiCmdQueue, &msg, OS_MESG_BLOCK);

        if (ret != 0 || msg == nullptr) {
            if (myNT) PreemptiveYield(myNT.get());
            continue;
        }

        OSIoMesg* ioMsg = reinterpret_cast<OSIoMesg*>(msg);
        s32 direction = OS_READ;

        if (ioMsg->hdr.type == 16 || ioMsg->hdr.type == 2) {
            direction = OS_WRITE;
        }

        osPiRawStartDma(direction, ioMsg->devAddr, ioMsg->dramAddr, ioMsg->size);

        if (ioMsg->hdr.retQueue != nullptr) {
            osSendMesg(ioMsg->hdr.retQueue, reinterpret_cast<OSMesg>(ioMsg), OS_MESG_NOBLOCK);
        }
    }

    s_n64_gil.unlock();
    return nullptr;
}

void osCreatePiManager(OSPri pri, OSMesgQueue *cmdQ, OSMesg *cmdBuf, s32 cmdMsgCnt) {
    s_hlePiCmdQueue = cmdQ;
    pthread_create(&s_hlePiMgrThread, nullptr, HLE_PiManagerWorker, nullptr);
    pthread_detach(s_hlePiMgrThread);
    LOGI("BKA-HLE: osCreatePiManager successfully generated.");
}

/* ============================================================
   6. SAFE AUDIO/VIDEO ENDPOINTS
   ============================================================ */

void osSpTaskLoad(OSTask *tp) {}

// MODIFIED: Route GFX tasks through the software RDP before signaling completion
void osSpTaskStartGo(OSTask *tp) {
    LOGI("BKA-RDP: osSpTaskStartGo type=%d data=%p size=%u", tp->t.type, tp->t.data_ptr, tp->t.data_size);
    if (tp == nullptr) return;
    if (tp->t.type == M_GFXTASK) {
        LOGI("BKA-RDP: GFX task data=%p size=%u", tp->t.data_ptr, tp->t.data_size);
        // Process the F3DEX display list and rasterize to gFramebuffers
        RSP_ProcessGfxTask(tp);
        // Signal completion so Thread 5 continues
        HLE_TriggerN64Event(1); // OS_EVENT_SP
        HLE_TriggerN64Event(3); // OS_EVENT_DP
        osSendMesg(&D_8027FBC8, NULL, OS_MESG_NOBLOCK);
    } else if (tp->t.type == M_AUDTASK) {
        HLE_TriggerN64Event(1); // OS_EVENT_SP
    }
}

void osSpTaskYield(void)                    {}
OSYieldResult osSpTaskYielded(OSTask *tp)   { return (OSYieldResult)0; }

s32 osAiSetNextBuffer(void *bufPtr, u32 size) {
    if (size == 0 || bufPtr == nullptr) return 0;
    HLE_TriggerN64Event(9); // OS_EVENT_AI
    return 0;
}

u32 osAiGetLength(void)              { return 0; }
s32 osAiSetFrequency(u32 frequency)  { return 0; }

/* ============================================================
   7. EEPROM / SAVE SYSTEM STUBS
   ============================================================ */

s32 osEepromProbe(OSMesgQueue *mq) { return 1; }
s32 osEepromLongRead(OSMesgQueue *mq, u8 address, u8 *buffer, int nbytes) { memset(buffer, 0, nbytes); return 0; }
s32 osEepromLongWrite(OSMesgQueue *mq, u8 address, u8 *buffer, int nbytes) { return 0; }
s32 osEepromRead(OSMesgQueue *mq, u8 address, u8 *buffer) { memset(buffer, 0, 8); return 0; }
s32 osEepromWrite(OSMesgQueue *mq, u8 address, u8 *buffer) { return 0; }

/* ============================================================
   8. SECURE ENGINE IGNITION
   ============================================================ */

extern uint8_t* gN64_RDRAM;
extern uint8_t* gN64_ROM_Base;

extern void func_80000450(int32_t arg0);

// Thread-safe wrapper for bkboot_inflate
extern "C" int bkboot_inflate_unlocked(void);

int bkboot_inflate(void) {
    pthread_mutex_lock(&g_inflateMutex);
    int result = bkboot_inflate_unlocked();
    pthread_mutex_unlock(&g_inflateMutex);
    return result;
}

void BKA_StartEngine(void) {
    LOGI("BKA-STUBS: Waiting for resource gate before engine ignition...");
    WaitForResourcesReady();

    LOGI("BKA-STUBS: Resource gate passed.");

    if (gN64_RDRAM == nullptr) {
        LOGE("BKA-STUBS: FATAL: gN64_RDRAM is null.");
        return;
    }

    if (gN64_ROM_Base == nullptr) {
        LOGE("BKA-STUBS: FATAL: gN64_ROM_Base is null. ResourceMgr failed to load ROM.");
        return;
    }

    if (!D_80007284 || !D_80007290 || !inbuf) {
        LOGE("BKA-STUBS: FATAL: Decompression buffers (D_80007284=%p, D_80007290=%p, inbuf=%p) are not initialized!",
             D_80007284, D_80007290, inbuf);
        return;
    }

    LOGI("BKA-STUBS: ROM verification successful. RDRAM=%p ROM=%p", gN64_RDRAM, gN64_ROM_Base);

    // GIL already held by NativeThreadWrapper

    LOGI("BKA-STUBS: Launching engine entry func_80000450.");
    func_80000450(0);
    LOGI("BKA-STUBS: Engine entry func_80000450 returned — game thread exited!");

    // s_n64_gil.unlock REMOVED — game threads manage GIL via BKA_FrameSyncHook();
}

void BKA_DropEngineLock(void)  { s_n64_gil.unlock(); }
void BKA_ClaimEngineLock(void) { s_n64_gil.lock(); }

} // end extern "C"

// -------------------------------------------------------------------------
// C++ linkage stubs for functions called from recompiled code
// -------------------------------------------------------------------------
// mainLoop stub REMOVED — real implementation in src/core1/code_0.c
void core1_loadOTR(uint8_t* data, size_t size) {}
int  func_80258A4C(void)                    { return 0; }
void func_8025A123(void)                    {}
void initInterruptTables(void)              {}