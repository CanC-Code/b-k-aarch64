/* linker_stubs.c — provides symbols for N64 functions without including
 * any N64 headers, avoiding type conflicts. All functions are weak stubs
 * using generic pointer types. */

#include <stdint.h>
#include <stdio.h>
#include <android/log.h>
typedef int8_t  s8;
typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int32_t  s32;
extern s32 osSendMesg(void *mq, void *msg, s32 flag);
typedef float    f32;
typedef uint64_t u64;
typedef int      n64_bool;

// Audio library
void alBnkfNew(void *f, void *table) {}
void alCSPSetBank(void *seqp, void *b) {}
void alCSPStop(void *seqp) {}
void alCSPSetSeq(void *seqp, void *seq) {}
void alCSPPlay(void *seqp) {}
void alCSPSetVol(void *seqp, s32 vol) { (void)vol; }
void alCSPSetTempo(void *seqp, s32 tempo) { (void)tempo; }
s32  alCSeqGetTicks(void *seq) { return 0; }
s32  alCSPGetTempo(void *seqp) { return 0; }
void alHeapInit(void *hp, void *base, s32 len) {}
void *alHeapDBAlloc(void *file, s32 line, void *hp, s32 num, s32 size) { return 0; }
void alLink(void *element, void *after) {}
void alUnlink(void *element) {}
void alEvtqNew(void *evtq, void *items, s32 itemCount) {}

// OS
void osInitialize(void) {}
u64  osGetTime(void) { return 0; }
u32  osViClock(void) { return 0; }
#define BKA_ADDR_MAP_SIZE 8192
static uint32_t s_bka_addr_key[BKA_ADDR_MAP_SIZE];
static void    *s_bka_addr_ptr[BKA_ADDR_MAP_SIZE];
static int       s_bka_addr_count = 0;

void bka_store_addr_mapping(uint32_t key, void *ptr) {
    for (int i = 0; i < s_bka_addr_count; i++) {
        if (s_bka_addr_key[i] == key) {
            s_bka_addr_ptr[i] = ptr;
            return;
        }
    }
    if (s_bka_addr_count < BKA_ADDR_MAP_SIZE) {
        s_bka_addr_key[s_bka_addr_count] = key;
        s_bka_addr_ptr[s_bka_addr_count] = ptr;
        s_bka_addr_count++;
    }
}

int bka_is_mapped(void* ptr) {
    uintptr_t addr = (uintptr_t)ptr;
    FILE* f = fopen("/proc/self/maps", "r");
    if (!f) return 0;
    char line[256];
    int result = 0;
    while (fgets(line, sizeof(line), f)) {
        uintptr_t start, end;
        if (sscanf(line, "%lx-%lx", &start, &end) == 2) {
            if (addr >= start && addr < end) {
                result = 1;
                break;
            }
        }
    }
    fclose(f);
    return result;
}

void* bka_lookup_addr_mapping(uint32_t key) {
    for (int i = 0; i < s_bka_addr_count; i++) {
        if (s_bka_addr_key[i] == key) {
            return s_bka_addr_ptr[i];
        }
    }
    return 0;
}

u32  osVirtualToPhysical(void *vaddr) {
    u32 key = (u32)(uintptr_t)vaddr;
    bka_store_addr_mapping(key, vaddr);
    __android_log_print(ANDROID_LOG_INFO, "BKA_GFX", "osVirtualToPhysical: vaddr=%p key=0x%08X", vaddr, key);
    return key;
}

// Graphics
void guMtxIdentF(void *mf) {}
void guMtxF2L(void *mf, void *m) {}

// Additional stubs
void osStopTimer(void *t) {}
s32  osSetTimer(void *t, u64 countdown, u64 interval, void *mq, void *msg) { return 0; }
u32  osClockRate(void) { return 0; }
u32  bkGetSR(void) { return 0; }
void bkmemcpy64(void *dst, void *src, u32 size) {}
void alEvtqFlushType(void *evtq, s32 type) {}
s32  __alCSeqNextDelta(void *seq, void *state) { return 0; }
void init_lpfilter(void *filter) {}
void alCopy(void *src, void *dst, s32 len) {}
s32  _doModFunc(s32 val, s32 mod, s32 rate) { return 0; }
s32  __alSeqNextDelta(void *seq, void *state) { return 0; }
void alEvtqPostEvent(void *evtq, void *item) {}
void alEvtqNextEvent(void *evtq, void *item) {}
void osDpSetStatus(u32 status) {}
u32 osDpGetStatus(void) { return 0; }
void *osViGetCurrentFramebuffer(void) { return 0; }

// Microcode globals
unsigned long long gspF3DEX_fifoTextStart[1];
unsigned long long gspF3DEX_fifoDataStart[1];
unsigned long long gspL3DEX_fifoTextStart[1];
unsigned long long gspL3DEX_fifoDataStart[1];

// Final remaining stubs
s32  alSeqGetTicks(void *seq) { return 0; }
void alSeqSetLoc(void *seq, s32 loc) {}
void rmonPrintf(const char *fmt, ...) {}
s32  osContGetReadData(void *pad) { extern void *gN64_ControllerData; if (pad && gN64_ControllerData) { memcpy(pad, gN64_ControllerData, 4); __android_log_print(ANDROID_LOG_INFO, "BKA_INPUT", "osContGetReadData: button=0x%04x stick_x=%d stick_y=%d", ((u16*)pad)[0], ((s8*)pad)[2], ((s8*)pad)[3]); } return 0; }
s32  osContInit(void *mq, void *status, void *pad) { if (status) ((u8*)status)[0] = 0x80; if (pad) ((u8*)pad)[0] = 0x80; return 0; }
s32  osContSetCh(u8 ch) { return 0; }
s32  osContStartReadData(void *mq) { __android_log_print(ANDROID_LOG_INFO, "BKA_INPUT", "osContStartReadData called mq=%p", mq); extern s32 osSendMesg(void *mq, void *msg, s32 flag); if (mq) osSendMesg(mq, (void*)1, 0); return 0; }
s32  osPiReadIo(u32 devAddr, u32 *data) { *data = 0; return 0; }
void guOrtho(void *m) {}
void guTranslate(void *m, f32 x, f32 y, f32 z) {}
void guRotate(void *m, f32 a, f32 x, f32 y, f32 z) {}
void bkmemset64(void *dst, u32 val, u32 size) {}
void *osViGetNextFramebuffer(void) { return 0; }
void osViBlack(u8 active) {}
s32  overlayManager_getLoadedID(void) { return 0; }
void overlayManager_load(s32 id) {}
void osSyncPrintf(const char *fmt, ...) {}
