#include "RT64Renderer.h"
#include "rt64_application.h"
#include "rt64_application_window.h"
#include <android/log.h>

extern uint8_t* gN64_RDRAM;
extern uint32_t* gN64_Reg_Base;  // if defined in lowlevel_bridge.cpp

using namespace RT64;

RT64Renderer& RT64Renderer::get() {
    static RT64Renderer instance;
    return instance;
}

void RT64Renderer::initialize() {
    if (initialized_ || !gN64_RDRAM) return;

    // Minimal Core structure with just RDRAM and dummy registers for now
    Core core = {};
    core.RDRAM = gN64_RDRAM;
    core.DMEM = (uint8_t*)calloc(0x1000, 1);
    core.IMEM = (uint8_t*)calloc(0x1000, 1);
    // Fill remaining pointer fields with null if not needed; can refine later.
    // Use gN64_Reg_Base if available, else allocate dummy arrays.
    // For simplicity, we'll allocate a dummy register area.
    static uint32_t dummyRegs[1024] = {0};
    core.MI_INTR_REG = &dummyRegs[0x00300008 / 4];
    core.DPC_START_REG = &dummyRegs[0x00001000 / 4];
    core.DPC_END_REG = &dummyRegs[0x00001004 / 4];
    core.DPC_CURRENT_REG = &dummyRegs[0x00001008 / 4];
    core.DPC_STATUS_REG = &dummyRegs[0x0000100C / 4];
    core.DPC_CLOCK_REG = &dummyRegs[0x00001010 / 4];
    core.DPC_BUFBUSY_REG = &dummyRegs[0x00001014 / 4];
    core.DPC_PIPEBUSY_REG = &dummyRegs[0x00001018 / 4];
    core.DPC_TMEM_REG = &dummyRegs[0x0000101C / 4];
    core.VI_STATUS_REG = &dummyRegs[0x00002000 / 4];
    core.VI_ORIGIN_REG = &dummyRegs[0x00002004 / 4];
    core.VI_WIDTH_REG = &dummyRegs[0x00002008 / 4];
    core.VI_INTR_REG = &dummyRegs[0x0000200C / 4];
    core.VI_V_CURRENT_LINE_REG = &dummyRegs[0x00002010 / 4];
    core.VI_TIMING_REG = &dummyRegs[0x00002014 / 4];
    core.VI_V_SYNC_REG = &dummyRegs[0x00002018 / 4];
    core.VI_H_SYNC_REG = &dummyRegs[0x0000201C / 4];
    core.VI_LEAP_REG = &dummyRegs[0x00002020 / 4];
    core.VI_H_START_REG = &dummyRegs[0x00002024 / 4];
    core.VI_V_START_REG = &dummyRegs[0x00002028 / 4];
    core.VI_V_BURST_REG = &dummyRegs[0x0000202C / 4];
    core.VI_X_SCALE_REG = &dummyRegs[0x00002030 / 4];
    core.VI_Y_SCALE_REG = &dummyRegs[0x00002034 / 4];

    ApplicationConfiguration appConfig;
    appConfig.detectDataPath = false;

    app_ = std::make_unique<Application>(core, appConfig);
    // Try to setup without a window? May fail, but we handle gracefully.
    app_->setup(0);

    initialized_ = true;
    __android_log_print(ANDROID_LOG_INFO, "RT64Renderer", "Initialized");
}

void RT64Renderer::shutdown() {
    app_.reset();
    initialized_ = false;
}

void RT64Renderer::processDisplayLists(uint8_t* rdram, uint32_t dlStart, uint32_t dlEnd, bool isHLE) {
    if (!initialized_ || !app_) return;
    app_->processDisplayLists(rdram, dlStart, dlEnd, isHLE);
}
