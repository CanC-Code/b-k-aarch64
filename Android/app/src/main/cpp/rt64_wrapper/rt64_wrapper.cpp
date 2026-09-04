#include "rt64_wrapper.h"
#include "rt64_application.h"
#include "rt64_application_window.h"
#include <android/native_window.h>
#include <android/log.h>

using namespace RT64;

struct RT64Context {
    Application* app;
};

RT64Handle rt64_init(void* window, uint32_t width, uint32_t height) {
    auto* ctx = new RT64Context();
    ctx->app = nullptr;

    Core core = {};
    core.RDRAM = (uint8_t*)calloc(0x1000000, 1);
    core.DMEM = (uint8_t*)calloc(0x1000, 1);
    core.IMEM = (uint8_t*)calloc(0x1000, 1);
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

    ctx->app = new Application(core, appConfig);
    ctx->app->setup(0);

    __android_log_print(ANDROID_LOG_INFO, "RT64Wrapper", "Initialized");
    return ctx;
}

void rt64_process_display_lists(RT64Handle handle, uint8_t* rdram, uint32_t dl_start, uint32_t dl_end, bool is_hle) {
    auto* ctx = static_cast<RT64Context*>(handle);
    if (!ctx || !ctx->app) return;
    ctx->app->processDisplayLists(rdram, dl_start, dl_end, is_hle);
}

void rt64_destroy(RT64Handle handle) {
    auto* ctx = static_cast<RT64Context*>(handle);
    if (!ctx) return;
    delete ctx->app;
    delete ctx;
}
