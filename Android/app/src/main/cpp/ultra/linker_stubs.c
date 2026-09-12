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


uintptr_t bka_get_mapped_end(void* ptr) {
    uintptr_t addr = (uintptr_t)ptr;
    FILE* f = fopen("/proc/self/maps", "r");
    if (!f) return 0;
    char line[256];
    uintptr_t start, end;
    while (fgets(line, sizeof(line), f)) {
        if (sscanf(line, "%lx-%lx", &start, &end) == 2) {
            if (addr >= start && addr < end) {
                fclose(f);
                return end;
            }
        }
    }
    fclose(f);
    return 0;
}

int bka_is_mapped(void* ptr) {
    uintptr_t addr = (uintptr_t)ptr;
    FILE* f = fopen("/proc/self/maps", "r");
    if (!f) return 0;
    char line[256];
    int result = 0;
    while (fgets(line, sizeof(line), f)) {
        uintptr_t start, end;
        char perms[5] = {0};
        if (sscanf(line, "%lx-%lx %4s", &start, &end, perms) == 3) {
            // Only accept regions that are readable.
            if (addr >= start && addr < end) {
                if (perms[0] == 'r') result = 1;
                break;
            }
        }
    }
    fclose(f);
    return result;
}

void* bka_lookup_addr_mapping_cside_impl(uint32_t key) {
    for (int i = 0; i < s_bka_addr_count; i++) {
        if (s_bka_addr_key[i] == key) {
            return s_bka_addr_ptr[i];
        }
    }
    return 0;
}

void* bka_lookup_addr_mapping_cside(uint32_t key) { return bka_lookup_addr_mapping_cside_impl(key); }

u32  osVirtualToPhysical(void *vaddr) {
    u32 key = (u32)(uintptr_t)vaddr;
    extern void bka_add_addr_mapping_c(uint32_t key, void *ptr);
    bka_add_addr_mapping_c(key, vaddr);
    static int s_reg_log = 0;
    if (s_reg_log++ < 30) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "MAPREG key=0x%08X vaddr=%p", key, vaddr);
    }
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
/* ------------------------------------------------------------------
 * The game carries its own GU implementations in src/core1/code_7F60.c
 * under the internal "_gu*" names. The original stubs were no-ops,
 * silently dropping every modelview rotation and translation. Delegate
 * to the real ones.
 * ------------------------------------------------------------------ */
extern void _guRotateF(f32 mf[4][4], f32 a, f32 x, f32 y, f32 z);
extern void _guTranslateF(f32 mf[4][4], f32 x, f32 y, f32 z);
extern void _guMtxF2L(f32 mf[4][4], void *m);

void guRotate(void *m, f32 a, f32 x, f32 y, f32 z) {
    f32 mf[4][4];
    _guRotateF(mf, a, x, y, z);
    _guMtxF2L(mf, m);
}

void guTranslate(void *m, f32 x, f32 y, f32 z) {
    f32 mf[4][4];
    _guTranslateF(mf, x, y, z);
    _guMtxF2L(mf, m);
}

void guOrtho(void *m, f32 l, f32 r, f32 b, f32 t, f32 n, f32 f, f32 scale) {
    f32 mf[4][4];
    int i, j;
    for (i = 0; i < 4; i++)
        for (j = 0; j < 4; j++)
            mf[i][j] = 0.0f;
    mf[0][0] =  2.0f / (r - l);
    mf[1][1] =  2.0f / (t - b);
    mf[2][2] = -2.0f / (f - n);
    mf[3][0] = -(r + l) / (r - l);
    mf[3][1] = -(t + b) / (t - b);
    mf[3][2] = -(f + n) / (f - n);
    mf[3][3] =  1.0f;
    _guMtxF2L(mf, m);
}
void bkmemset64(void *dst, u32 val, u32 size) {}
void *osViGetNextFramebuffer(void) { return 0; }
void osViBlack(u8 active) {}
s32  overlayManager_getLoadedID(void) { return 0; }
void overlayManager_load(s32 id) {}
void osSyncPrintf(const char *fmt, ...) {}
