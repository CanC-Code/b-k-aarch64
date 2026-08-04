#include <cstdint>
#include <cstdlib>

#define RECOMP_SYMBOL __attribute__((used)) __attribute__((visibility("default")))

extern "C" {
    // ------------------------------------------------------------
    // 1. Initialization Bridge
    // ------------------------------------------------------------
    void InitN64Registers(const char* assetDir);
    
    RECOMP_SYMBOL void InitHardwareRegs() {
        InitN64Registers(nullptr);
    }

    // ------------------------------------------------------------
    // 2. Engine Globals
    // ------------------------------------------------------------
    RECOMP_SYMBOL uint32_t __libm_qnan_f = 0x7FC00000;
    RECOMP_SYMBOL uintptr_t core1_VRAM           = 0x80001000;
    RECOMP_SYMBOL uintptr_t core2_TEXT_START     = 0x00000000;
    RECOMP_SYMBOL uintptr_t gOverlayTable        = 0x01200000;

    // ------------------------------------------------------------
    // 3. Level/Asset ROM Markers (The symbols causing the build errors)
    // ------------------------------------------------------------
    // Core/Common
    RECOMP_SYMBOL uintptr_t core1_rzip_ROM_START = 0x00001050;
    RECOMP_SYMBOL uintptr_t core1_rzip_ROM_END   = 0x000E0000;
    RECOMP_SYMBOL uintptr_t core2_rzip_ROM_START = 0x000F0000;
    RECOMP_SYMBOL uintptr_t core2_rzip_ROM_END   = 0x001F0000;

    // Levels
    RECOMP_SYMBOL uintptr_t SM_rzip_ROM_START    = 0x00400000;
    RECOMP_SYMBOL uintptr_t SM_rzip_ROM_END      = 0x00410000;
    RECOMP_SYMBOL uintptr_t MM_rzip_ROM_START    = 0x00500000;
    RECOMP_SYMBOL uintptr_t MM_rzip_ROM_END      = 0x00510000;
    RECOMP_SYMBOL uintptr_t TTC_rzip_ROM_START   = 0x00600000;
    RECOMP_SYMBOL uintptr_t TTC_rzip_ROM_END     = 0x00610000;
    RECOMP_SYMBOL uintptr_t CC_rzip_ROM_START    = 0x00700000;
    RECOMP_SYMBOL uintptr_t CC_rzip_ROM_END      = 0x00710000;
    RECOMP_SYMBOL uintptr_t BGS_rzip_ROM_START   = 0x00800000;
    RECOMP_SYMBOL uintptr_t BGS_rzip_ROM_END     = 0x00810000;
    RECOMP_SYMBOL uintptr_t FP_rzip_ROM_START    = 0x00900000;
    RECOMP_SYMBOL uintptr_t FP_rzip_ROM_END      = 0x00910000;
    RECOMP_SYMBOL uintptr_t GV_rzip_ROM_START    = 0x00A00000;
    RECOMP_SYMBOL uintptr_t GV_rzip_ROM_END      = 0x00A10000;
    RECOMP_SYMBOL uintptr_t MMM_rzip_ROM_START   = 0x00B00000;
    RECOMP_SYMBOL uintptr_t MMM_rzip_ROM_END     = 0x00B10000;
    RECOMP_SYMBOL uintptr_t RBB_rzip_ROM_START   = 0x00C00000;
    RECOMP_SYMBOL uintptr_t RBB_rzip_ROM_END     = 0x00C10000;
    RECOMP_SYMBOL uintptr_t CCW_rzip_ROM_START   = 0x00D00000;
    RECOMP_SYMBOL uintptr_t CCW_rzip_ROM_END     = 0x00D10000;

    // Special
    RECOMP_SYMBOL uintptr_t lair_rzip_ROM_START      = 0x00E00000;
    RECOMP_SYMBOL uintptr_t lair_rzip_ROM_END        = 0x00E10000;
    RECOMP_SYMBOL uintptr_t fight_rzip_ROM_START     = 0x00F00000;
    RECOMP_SYMBOL uintptr_t fight_rzip_ROM_END       = 0x00F10000;
    RECOMP_SYMBOL uintptr_t cutscenes_rzip_ROM_START = 0x01000000;
    RECOMP_SYMBOL uintptr_t cutscenes_rzip_ROM_END   = 0x01010000;
    RECOMP_SYMBOL uintptr_t emptyLvl_rzip_ROM_START  = 0x01100000;
    RECOMP_SYMBOL uintptr_t emptyLvl_rzip_ROM_END    = 0x01110000;
}
