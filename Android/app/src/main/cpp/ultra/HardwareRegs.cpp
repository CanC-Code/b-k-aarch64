#include "HardwareRegs.h"
#include <stdlib.h>
#include <string.h>
#include <android/log.h>
#include <sys/mman.h>

extern "C" {
    uint8_t* gN64_RDRAM    = nullptr;
    uint32_t* gN64_Reg_Base = nullptr;
}

static uint32_t s_regFile[0x50000 / 4]; // Large enough for register space

extern "C" void InitN64Registers(const char* assetDir) {
    if (gN64_RDRAM != nullptr) return;

    // Use mmap instead of calloc – mmap respects android:memtagMode="off"
    // so this memory will be untagged, preventing MTE crashes when the
    // game stores pointers inside RDRAM and later dereferences them.
    gN64_RDRAM = static_cast<uint8_t*>(mmap(nullptr, 0x1000000,
                                            PROT_READ | PROT_WRITE,
                                            MAP_PRIVATE | MAP_ANONYMOUS,
                                            -1, 0));
    if (gN64_RDRAM == MAP_FAILED) {
        // fallback to calloc if mmap fails (shouldn't happen on Android)
        gN64_RDRAM = static_cast<uint8_t*>(calloc(0x1000000, 1));
    }
    gN64_Reg_Base = s_regFile;
    memset(s_regFile, 0, sizeof(s_regFile));

    // After setting the base, trigger the linker bridge to map the specific symbols
    extern void BKA_Register_Init_Bridge(const char*);
    BKA_Register_Init_Bridge(assetDir);
}
