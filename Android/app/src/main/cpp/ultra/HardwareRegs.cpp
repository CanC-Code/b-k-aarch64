#include <sys/prctl.h>
#include "HardwareRegs.h"
#include <stdlib.h>
#include <string.h>
#include <android/log.h>

extern "C" {
    uint8_t* gN64_RDRAM    = nullptr;
    uint32_t* gN64_Reg_Base = nullptr;
}

static uint32_t s_regFile[0x50000 / 4]; // Large enough for register space

extern "C" void InitN64Registers(const char* assetDir) {
    if (gN64_RDRAM != nullptr) return;

    prctl(PR_SET_TAGGED_ADDR_CTRL, PR_TAGGED_ADDR_ENABLE, 0, 0, 0);
    gN64_RDRAM = static_cast<uint8_t*>(calloc(0x1000000, 1));
    gN64_Reg_Base = s_regFile;
    memset(s_regFile, 0, sizeof(s_regFile));

    // After setting the base, trigger the linker bridge to map the specific symbols
    extern void BKA_Register_Init_Bridge(const char*);
    BKA_Register_Init_Bridge(assetDir);
}
