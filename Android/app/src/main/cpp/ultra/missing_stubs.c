// File: Banjo-android-realignment/Android/app/src/main/cpp/ultra/missing_stubs.c
//
// LAST-RESORT fallbacks only.
//
// Rules:
//   - Do NOT define anything that has a real implementation in:
//       exceptasm.cpp    (initInterruptTables, __osPopThread, __osEnqueueThread,
//                         __osDispatchThread, __osEnqueueAndYield)
//       setintmask.cpp   (osSetIntMask)
//       libm_vals.cpp    (__libm_qnan_f)
//       lowlevel_bridge.cpp (osPiReadIo, osPiWriteIo, g_active_fb_offset,
//                            gFramebuffers)
//       audio_bridge.cpp (n_alSynAddPlayer, n_alSynRemovePlayer, etc.)
//       stubs.cpp        (initInterruptTables fallback, stub_void, etc.)
//
//   CMakeLists.txt lists this file LAST so the linker always prefers
//   the real implementations above when --allow-multiple-definition is set.

// Forward declarations for print/font stubs
void print_init(void);
void print_getLettersFromFont(void* arg0, void* arg1);
void func_802E5F38(void);
void func_802E5F10(void);

// gsworld state getters/setters forward declarations

void gsworld_setEnableUpdate(int value);

void gsworld_setEnableDraw(int value);

int gsworld_getEnableUpdate(void);

int gsworld_getEnableDraw(void);

#include <string.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <android/log.h>

#define LOG_TAG "BKA_STUBS"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

typedef uint32_t OSIntMask;
typedef int32_t  s32;
typedef uint8_t  u8;

// -----------------------------------------------------------------------
// OS / Hardware
// -----------------------------------------------------------------------
OSIntMask __osDisableInt(void) { return 0; }
void      __osRestoreInt(OSIntMask mask) { (void)mask; }
void bzero(void *s, int n)                    { memset(s, 0, (size_t)n); }
void bcopy(const void *src, void *dest, int n){ memmove(dest, src, (size_t)n); }
void osWritebackDCache(void *vaddr, int32_t nbytes)  { (void)vaddr; (void)nbytes; }
void osInvalICache(void *vaddr, int32_t nbytes)       { (void)vaddr; (void)nbytes; }
void osInvalDCache(void *vaddr, int32_t nbytes)       { (void)vaddr; (void)nbytes; }
void osWriteBackDCacheAll(void)                       {}
void __osInitialize_autodetect(void)                  {}
void __osCleanupThread(void) {}
uint32_t osGetCount(void)              { static uint32_t counter = 0; return counter += 1000; }
uint32_t __osGetSR(void)               { return 0; }
uint32_t ___osGetSR(void)              { return 0; }
void     __osSetSR(uint32_t sr)        { (void)sr; }
void     __osSetFpcCsr(uint32_t csr)   { (void)csr; }
void     __osSetCompare(uint32_t val)  { (void)val; }
void     osMapTLBRdb(void)             {}
uint32_t __osProbeTLB(void* a)         { (void)a; return 0; }
#define PI_STATUS_DMA_BUSY  0x01
uint32_t osPiGetStatus(void)           { return 0; }
void osViSetSpecialFeatures(u32 func)                { (void)func; }
void osViSwapBuffer(void *vaddr)                     { (void)vaddr; }
s32 inflate(void) { return 0; }

// -----------------------------------------------------------------------
// Misc functions
// -----------------------------------------------------------------------
int  func_8025C29C(void) { return 0; }
int  func_80253010(void) { return 0; }
void func_80253034(void *dst, int val, size_t size) { memset(dst, val, size); }
void func_8026A2E0(void) {}

// -----------------------------------------------------------------------
// Global variables
// -----------------------------------------------------------------------
#define BK_HEAP_SIZE 0x211120
u8 D_8002D500[BK_HEAP_SIZE] __attribute__((aligned(16)));
uint64_t D_8023DA00[4] __attribute__((aligned(16)));
uint32_t D_803FFE00[4] = {0, 0, 0, 0};
uint8_t D_8000E800[0x100000] __attribute__((aligned(16)));
uint64_t D_803FFE10[15] __attribute__((aligned(8)));
uint8_t D_803FBE00[0x2000] __attribute__((aligned(16)));

void *n64_malloc(s32 size)   { return malloc(size); }
void *n64_realloc(void *ptr, s32 size) { return realloc(ptr, size); }
void n64_free(void *ptr)     { free(ptr); }

// -----------------------------------------------------------------------
// ROM symbols
// -----------------------------------------------------------------------
int crc_ROM_START            = 0;
int soundfont1ctl_ROM_START  = 0;
int soundfont1ctl_ROM_END    = 0;
int soundfont1tbl_ROM_START  = 0;
int soundfont2ctl_ROM_START  = 0;
int soundfont2ctl_ROM_END    = 0;
int soundfont2tbl_ROM_START  = 0;
int assets_ROM_START         = 0x5E90;
int boot_bk_boot_ROM_START   = 0;
int boot_bk_boot_ROM_END     = 0;
int n_aspMainTextStart        = 0;
int n_aspMainDataStart        = 0;
int gSPF3DEX_fifoTextStart   = 0;
int gSPF3DEX_fifoDataStart   = 0;
int gSPL3DEX_fifoTextStart   = 0;
int gSPL3DEX_fifoDataStart   = 0;
int gSPL3DEX_fifoTextEnd     = 0;

// -----------------------------------------------------------------------
// Overlay VRAM
// -----------------------------------------------------------------------
#define DEFINE_OVERLAY_VRAM(name, vram_start, vram_end) \
    u32 name##_VRAM        = vram_start; \
    u32 name##_VRAM_END    = vram_end;   \
    u32 name##_ROM_START   = 0; \
    u32 name##_ROM_END     = 0; \
    u32 name##_TEXT_START  = 0; \
    u32 name##_TEXT_END    = 0; \
    u32 name##_DATA_START  = 0; \
    u32 name##_RODATA_END  = 0; \
    u32 name##_BSS_START   = 0; \
    u32 name##_BSS_END     = 0;

DEFINE_OVERLAY_VRAM(core2,     0x80286F90, 0x80386DD0)
DEFINE_OVERLAY_VRAM(emptyLvl,  0x80386DD0, 0x80386DD0)
DEFINE_OVERLAY_VRAM(CC,        0x80386DD0, 0x8038A9E0)
DEFINE_OVERLAY_VRAM(MMM,       0x80386DD0, 0x8038CF10)
DEFINE_OVERLAY_VRAM(GV,        0x80386DD0, 0x803924F0)
DEFINE_OVERLAY_VRAM(TTC,       0x80386DD0, 0x8038E120)
DEFINE_OVERLAY_VRAM(MM,        0x80386DD0, 0x8038A680)
DEFINE_OVERLAY_VRAM(BGS,       0x80386DD0, 0x80391C30)
DEFINE_OVERLAY_VRAM(RBB,       0x80386DD0, 0x80391CD0)
DEFINE_OVERLAY_VRAM(FP,        0x80386DD0, 0x80393FD0)
DEFINE_OVERLAY_VRAM(CCW,       0x80386DD0, 0x803907D0)
DEFINE_OVERLAY_VRAM(SM,        0x80386DD0, 0x8038C010)
DEFINE_OVERLAY_VRAM(cutscenes, 0x80386DD0, 0x8038F3D0)
DEFINE_OVERLAY_VRAM(lair,      0x80386DD0, 0x80395E50)
DEFINE_OVERLAY_VRAM(fight,     0x80386DD0, 0x80393390)

u32 core1_VRAM     = 0x8023DA20;
u32 core1_VRAM_END = 0x80286F90;

// -----------------------------------------------------------------------
// Audio/SFX stubs
// -----------------------------------------------------------------------
void gcsfx_playWithPitch(int a, float b, int c, float d)  { (void)a; (void)b; (void)c; (void)d; }
void func_8030E878(void)                                   {}
int  sfx_playFadeShorthand(void)                           { return 0; }
void gcsfx_playAtSampleRate(int a, int b, int c)           { (void)a; (void)b; (void)c; }
void func_8030E624(int a, float b, int c)                  { (void)a; (void)b; (void)c; }
void gcsfx_play(int a, float b, int c)                     { (void)a; (void)b; (void)c; }
void sfxSource_triggerCallbackByIndex(int a)               { (void)a; }
void func_8030E760(void)                                   {}
void func_8030DD90(int a, int b)                           { (void)a; (void)b; }
void sfxsource_playSfxAtVolume(int a, float b)             { (void)a; (void)b; }
void sfxsource_setSfxId(int a, int b)                      { (void)a; (void)b; }
void sfxSource_setunk43_7ByIndex(int a, int b)              { (void)a; (void)b; }
void sfxsource_setSampleRate(int a, int b)                 { (void)a; (void)b; }
void sfxSource_func_8030E2C4(int a)                        { (void)a; }
void sfxsource_freeSfxsourceByIndex(int a)                 { (void)a; }
int  sfxsource_createSfxsourceAndReturnIndex(void)         { return 0; }
void func_8030E9FC(void)                                   {}
void func_8030EA54(void)                                   {}
void func_8030E730(void)                                   {}
void func_8030DBFC(void)                                   {}
void sfxsource_set_fade_distances(int a, float b, float c) { (void)a; (void)b; (void)c; }
void sfxsource_set_position(int a, int b)                  { (void)a; (void)b; }
void func_8030E6D4(void)                                   {}
void func_8030ED2C(void)                                   {}
void func_8030DB04(void)                                   {}
void func_8030E200(int a)                                  { (void)a; }
void func_8030E0FC(void)                                   {}
void func_8030E3FC(int a)                                  { (void)a; }
void func_8030E58C(void)                                   {}
void sfxsource_playHighPriority(int a)                     { (void)a; }
void func_8030E988(void)                                   {}
void func_8030ED70(void)                                   {}
void sfxSource_setCallbackByIndex(int a, int b)            { (void)a; (void)b; }
void func_8030E5F4(void)                                   {}
void func_8030EB88(void)                                   {}
void func_8030EAAC(void)                                   {}
void func_8030E560(void)                                   {}
void func_8030E4E4(void)                                   {}
void func_8030EBC8(void)                                   {}
void func_8030E04C(void)                                   {}
void func_8030EB00(void)                                   {}
void func_8030EC20(void)                                   {}
void func_8030E9C4(void)                                   {}
void func_8030DFF0(void)                                   {}
void func_8030DFB4(void)                                   {}
void func_8030ED0C(void)                                   {}
void func_8030EDAC(void)                                   {}
int  sfxSource_getSampleRate(int a)                         { (void)a; return 0; }
void func_8030DE44(void)                                   {}
void func_8030E704(void)                                   {}
void func_8030DCCC(void)                                   {}

// -----------------------------------------------------------------------
// Music / print / graphics stubs
// -----------------------------------------------------------------------
void coMusicPlayer_init(void)  {}
void coMusicPlayer_free(void)  {}
void coMusicPlayer_update(void) {}
void itemPrint_init(void)  {}
void itemPrint_update(void) {}
void itemPrint_free(void) {}
void itemPrint_draw(void *a, void *b, void *c) { (void)a; (void)b; (void)c; }
void itemPrint_defrag(void) {}
void func_80253208(void *a, int b, int c, int d, int e, void *f) { (void)a; (void)b; (void)c; (void)d; (void)e; (void)f; }
void zBuffer_set(void *a)                           { (void)a; }
void func_802476EC(void *a)                         { (void)a; }
void func_802E67AC(void) {}
void func_802E67C4(void) {}
void func_802E53EC4(void *a, void *b) { (void)a; (void)b; }
void printbuffer_draw(void *a, void *b, void *c) { (void)a; (void)b; (void)c; }
void printbuffer_defrag(void) {}
void depthbuffer_enable(int a) { (void)a; }
void modelRender_init(void) {}
void modelRender_free(void) {}
void modelRender_defrag(void) {}
void viewport_reset(void) {}
void viewport_setNearAndFar(float a, float b) { (void)a; (void)b; }
void viewport_setPosition_f3(float a, float b, float c) { (void)a; (void)b; (void)c; }
void viewport_setRotation_f3(float a, float b, float c) { (void)a; (void)b; (void)c; }
void viewport_moveAlongZAxis(float a) { (void)a; }
void viewport_update(void) {}
void viewport_debug(void) {}
void viewport_pushFramebufferExtendsToVpStack(void) {}
void func_8033B5FC(void) {}
void func_8033B61C(void) {}
void func_8033B268(void) {}
void mapSavestate_defrag_all(void) {}
void gctransition_defrag(void) {}
void comusic_defrag(void) {}
void func_80350E00(void) {}

// NOTE: The following functions are NO LONGER STUBBED — their real
// implementations from code_5DBC0.c and print.c are used instead:
//   print_init()      — initializes the font system
//   func_802E5F38()   — initializes the print buffer state
//   func_802E5F10()   — builds Gfx display list commands for text

// -----------------------------------------------------------------------
// Misc game stubs
// -----------------------------------------------------------------------
void func_8025A9D4(int a, int b) { (void)a; (void)b; }
void func_8025A7DC(int a) { (void)a; }
void func_8025A23C(int a) { (void)a; }
void func_8024E698(int a) { (void)a; }
void func_8024F150(void) {}
void func_8024F764(int a) { (void)a; }
void func_8024F7C4(int a) { (void)a; }
void func_8024FB8C(void) {}
int func_803226E8(int a) { (void)a; return 0; }
int func_80322914(void) { return 0; }
void func_8025A430(int a, int b, int c) { (void)a; (void)b; (void)c; }
void func_8025A2B0(void) {}
int controller_getStartButton(int a) { (void)a; return 0; }
void func_80334E1C(int a, int b) { (void)a; (void)b; }
void func_80323140(int a, int b) { (void)a; (void)b; }
void func_8032278C(void) {}
int func_8034BDA4(int a, int b) { (void)a; (void)b; return 0; }
void func_80346CA8(void) {}
void func_8030C1A0(void) {}
void func_8030C204(void) {}
void gcpausemenu_init(void) {}
void gcpausemenu_free(void) {}
int gcpausemenu_80314B00(void) { return 1; }
int gcPauseMenu_update(void) { return 0; }
int cutscenetrigger_update(void) { return 0; }
int gctransition_8030BDC0(void) { return 0; }
int gctransition_done(void) { return 1; }
void gctransition_8030BEA4(int a) { (void)a; }
void gctransition_8030BD4C(void) {}
void gctransition_8030BE60(void) {}
void gctransition_update(void) {}
void gctransition_draw(void *a, void *b, void *c) { (void)a; (void)b; (void)c; }
int func_8028F070(void) { return 1; }
int func_8028EC04(void) { return 0; }
int player_isDead(void) { return 0; }
void mapSavestate_apply(int a) { (void)a; }
void mapSavestate_save(int a) { (void)a; }
int gsworld_get_map(void) { return 0; }
void sns_save_and_update_global_data(void) {}
void func_8030D86C(void) {}
void func_80322764(void) {}
void timedFuncQueue_init(void) {}
void func_802F9CD8(void) {}
void func_8031B62C(void) {}
void defragManager_init(void) {}
void animCache_init(void) {}
void rand_reset(void) {}
void scissorBox_setDefault(void) {}
void func_80253FE8(void) {}
void time_reset(void) {}
void func_8033DC04(void) {}
void clearScoreStates(void) {}
void savedata_init(void) {}
void func_802E3854(void) {}
void func_802E3800(void) {}
void func_8033DC10(void) {}
void func_80324C58(void) {}
void picturebox_init(void) {}
void picturebox_free(void) {}
void func_802FA508(void) {}
void func_802E49E0(void) {}
int func_802E4A08(void) { return 0; }
int func_8032056C(void) { return 1; }
int func_8032190C(void) { return 0; }
int levelSpecificFlags_validateCRC1(void) { return 1; }
int dummy_func_80320248(void) { return 1; }
int func_80320240(void) { return 1; }
int map_getLevel(int a) { (void)a; return 0; }
int level_get(void) { return 0; }
void func_80321854(void) {}
void func_8030AFD8(int a) { (void)a; }


// =======================================================================
// gsworld state getters/setters
// =======================================================================
static int sEnableUpdate = 1;
static int sEnableDraw = 1;

void gsworld_setEnableUpdate(int value) { sEnableUpdate = value; }
void gsworld_setEnableDraw(int value)   { sEnableDraw = value; }
int gsworld_getEnableUpdate(void)       { return sEnableUpdate; }
int gsworld_getEnableDraw(void)         { return sEnableDraw; }

// =======================================================================
// Memory management stubs for AnimTextureListCache and freelist
// =======================================================================
void AnimTextureListCache_init(void) {
    // Safe stub - prevents crash from uninitialized freelist
}

void AnimTextureListCache_free(void) {
    // Safe stub
}

void freelist_clear(void *ptr) {
    // Safe stub - prevents crash from invalid memory access
    (void)ptr;
}

void *freelist_new(size_t size) {
    // Return NULL or a dummy pointer
    (void)size;
    return NULL;
}
