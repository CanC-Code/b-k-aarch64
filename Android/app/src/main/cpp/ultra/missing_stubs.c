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
void print_init(void) {}
void* print_getLettersFromFont(void* arg0, void* arg1) { return calloc(1, 256); }
void func_802E5F38(void) {}
void func_802E5F10(void);

// gsworld state getters/setters forward declarations



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
// s32 inflate(void) { return 0; } -- using real inflate.c

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
    u32 name##_VRAM_END    = vram_end; \
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
int g_diag_assetId = 0;
void* g_diag_cfile = NULL;
int g_diag_csize = 0;

// -----------------------------------------------------------------------
int g_diag_null_task = 0;
void particleEmitter_setModel(void* a, int b) {}
int g_diag_mesh_count = 0;
void* g_diag_mesh_ptr = NULL;
void playerModel_set(void) {}
int g_diag_thread5_loop = 0;
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
void func_8030A078(void) {}
u32 func_80320250(void) { return 0; }
void func_803202D0(void) {}
s32 func_80320320(void) { return 0; }
void func_803203A0(void) {}
int levelSpecificFlags_get(s32 a) { return 0; }
void _levelSpecificFlags_updateCRC1(void) {}
void _levelSpecificFlags_updateCRC2(void) {}
void levelSpecificFlags_clear(void) {}
void levelSpecificFlags_set(s32 a, s32 b) {}
void levelSpecificFlags_setN(s32 a, s32 b, s32 c) {}
int levelSpecificFlags_validateCRC2(void) { return 1; }
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

int gsworld_getEnableUpdate(void)       { return sEnableUpdate; }
int gsworld_getEnableDraw(void)         { return sEnableDraw; }

// =======================================================================
// Stubs for symbols from excluded inflate.c and N64 hardware functions

// =======================================================================
// Stubs for symbols from excluded inflate.c and N64 hardware functions
// =======================================================================

// Huffman table
struct huft_s { unsigned char e, b; unsigned short n; };
struct huft_s gGlobalHuffTable[1];

// Inflate globals
u32 inflate_crc1, inflate_crc2;
u8 *inflate_inbuf, *inflate_slide;
void *inflate_huft;
u32 inflate_wp, inflate_inptr;

// N64 globals
// Real N64 heap buffer - game code accesses as EmptyHeapBlock array
unsigned char gHeapBase[0x211120];
struct { u32 text_checksum1, text_checksum2, data_checksum1, data_checksum2; } gChecksumsCore1;
OSMesgQueue D_8027FBC8;

// N64 SDK functions
s32 osMotorInit(OSMesgQueue *mq, OSPfs *pfs, int channel) { (void)mq; (void)pfs; (void)channel; return 0; }
s32 osMotorStart(OSPfs *pfs) { (void)pfs; return 0; }
s32 osMotorStop(OSPfs *pfs) { (void)pfs; return 0; }
s32 osPfsInit(OSMesgQueue *mq, OSPfs *pfs, int channel) { (void)mq; (void)pfs; (void)channel; return 0; }
void osWritebackDCacheAll(void) {}
void overlayManager_loadCore2(void) {}
void overlayManagerloadCore2(void) {}
int bkboot_inflate_unlocked(void) { return 0; }
f32 alCents2Ratio(s32 cents) { (void)cents; return 1.0f; }

// =======================================================================

// Minimal heap initialization - called before first n64_malloc

// =======================================================================
// Memory allocator wrappers — redirect N64 heap to system malloc
// =======================================================================
#include <stdlib.h>

// =======================================================================
// N64 Memory Allocator — redirect to system malloc
// =======================================================================
void *n64_malloc(s32 size) {
#include <stdlib.h>
    (void)size;
    static size_t totalAlloc = 0; totalAlloc += size; if (size > 1048576) __android_log_print(ANDROID_LOG_WARN, "BKA_MEM", "n64_malloc: large alloc %d bytes, total=%zu", size, totalAlloc);
    void *ptr = malloc((size_t)size);
    if (ptr) memset(ptr, 0, (size_t)size);
    return ptr;
}
void n64_free(void *ptr) { free(ptr); }
void *n64_realloc(void *ptr, s32 size) { return realloc(ptr, (size_t)size); }

// heap_init is a no-op
void heap_init(void) {}
void func_802546FC(void) {}

// Memory management stubs (from excluded memory.c)
void defrag(void) {}
void *defrag_asset(void *ptr) { return ptr; }
s32 heap_get_size(void) { return 0x211120; }
s32 heap_get_occupied_size(void) { return 0; }
void func_80255198(void) {}
void func_80255524(void) {}
void func_80255ACC(void) {}
void func_8025484C(void) {}
void func_80254898(void) {}
void func_80254BD0(void) {}
void func_802559A0(void) {}
void func_80254BC4(void) {}
void func_802555C4(void) {}
void func_802555D0(void) {}
void func_80255B08(void) {}
s32 func_8025498C(s32 size) { (void)size; return 1; }
void func_80254C98(void) {}
void func_80255170(void) {}
void func_80255A14(void) {}
void func_80255A04(void) {}
void func_802546E4(void) {}
void func_80255AE4(void) {}
void func_80255888(void) {}

// SNS (Save/Notify System) stubs — not needed for rendering
void sns_find_and_parse_payload(void) {}
void sns_write_payload_over_heap(void) {}
void sns_init_base_payloads(void) {}
void snspayload_append_key_to_outgoing_payload(void *payload, s32 key) {}
void snspayload_rewind_outgoing(void) {}
void snspayload_finalise_outgoing_payload(void *payload) {}

extern void ResourceMgr_HandleDma(void* dramAddr, u32 devAddr, u32 size);
void piMgr_read(void *vaddr, s32 devaddr, s32 size) {
    if (!vaddr || size <= 0) return;
    ResourceMgr_HandleDma(vaddr, devaddr, size);
}
void piMgr_init(void) {}

//// Bypass world init to reach mainLoop for RDP testing
//extern struct { s32 unk0; s32 game_mode; } D_8037E8E0;
//void func_802E4214(s32 map_id) { 
//    extern void gsworld_set(s32 map, s32 arg1, s32 arg2);
//    gsworld_set(map_id, 0, 0);
//}
//void func_802E38E8(s32 map, s32 exit, s32 reset) { (void)map; (void)exit; (void)reset; }
void func_8023DA9C_stub(s32 arg0) { (void)arg0; }
//void func_802E4170(void) {}
void ucode_load(void) {}
void ucode_stub1(void) {}
void ucode_stub3(void) {}
void ucode_getPtrAndSize(void **ptr, u32 *size) { *ptr = NULL; *size = 0; }


// Remaining stubs from excluded files (ml.c, bamotor.c, controller.c)
void func_80258A4C(void) {}
void func_80256E24(void) {}
void func_8025715C(void) {}
void func_80256AB4(void) {}
void func_80256C60(void) {}
void func_80257204(void) {}
void func_80250E94(void) {}
void func_80250D94(void) {}
void ml_timer_update(void) {}
void ml_vec3f_interpolate_fast(void *a, void *b, void *c, float d) {}
void ml_vec3f_diff_copy(void *a, void *b, void *c) {}
void ml_vec3f_pitch_rotate_copy(void *a, void *b, void *c, float d) {}
void ml_vec3f_assign(void *a, void *b) {}
void ml_vec3f_horizontal_distance_zero_likely(void) {}
void ml_vec3f_distance(void) {}
void mlAbsF(void) {}
void ml_map_f(void) {}
void controller_getJoystick(void) {}
void controller_copyFaceButtons(void) {}

// Additional stubs for excluded files
void gctransition_reset(void) {}
void pfsManager_update(void) {}
void baMotor_80250C08(void) {}
void audioManager_getExtraDMAMesg(void) {}
void *audioManager_getDMANotifyMesgQueue(void) { return NULL; }
void *audioManager_getALHeapInfo(void) { return NULL; }
void audioManager_setupSeqp(void *a, void *b, void *c, void *d) {}
void viMgr_setActiveFramebuffer(int a) {}
void ml_vec3f_set_length_copy(void *a, void *b, float c) {}
void ml_vec3f_diff(void *a, void *b, void *c) {}
float ml_vec3f_dot_product(void *a, void *b) { return 0.0f; }

// More stubs from excluded files
void ml_vec3f_normalize_copy(void *a, void *b) {}
void viMgr_func_8024BFAC(void) {}
void *audioManager_getFrameMesgQueue(void) { return NULL; }
void baMotor_80250FC0(void) {}
void pfsManager_getStartReadData(void) {}
void viMgr_registerSignalMesg(void *a, void *b) {}
int ml_vec3w_inside_box_w(void *a, void *b, void *c) { return 0; }
void func_8024F35C(void) {}
void *pfsManager_getFrameReplyQ(void) { return NULL; }
float ml_sin_deg(float a) { return 0.0f; }
float ml_cos_deg(float a) { return 0.0f; }

// Remaining stubs from excluded files (baMotor, viMgr, pfsManager, audioManager, ml)
void baMotor_80250E94(void) {}
void baMotor_80250D94(void) {}
void viMgr_clearFramebuffers(void) {}
void viMgr_init(void) {}
void pfsManager_init(void) {}
void baMotor_init(void) {}
void audioManager_init(void) {}
void ml_init(void) {}

// Remaining stubs from baMotor, controller, and misc
void baMotor_80250E6C(void) {}
void controller_copySideButtons(void) {}
void func_8024E6E0(void) {}
void func_80257F18(void) {}
void func_80257A44(void) {}
void ml_sub_delta_time(void) {}

// Final remaining stubs
int getOtherFramebuffer(void) { return 1; }
void func_8024F3F4(void) {}
void func_8024E420(void) {}
void gctransition_8030BD88(void) {}
void viMgr_func_8024C1B4(void) {}
void viMgr_func_8024BF94(void) {}
void viMgr_func_8024C1DC(void) {}
void func_8024F180(void) {}
void viMgr_func_8024BD94(void) {}
void func_8024F224(void) {}
void pfsManager_getFirstControllerFaceButtonState(void) {}
void func_8024E640(void) {}
void func_8024E5E8(void) {}
int gctransition_active = 0;
int pfsManager_contErr = 0;
void func_80254008(void) {}
//int func_802E4424(void) { return 1; }
