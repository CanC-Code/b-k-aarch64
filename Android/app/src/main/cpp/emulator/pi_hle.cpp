#include <stdint.h>
#include <android/log.h>
#include "n64_types.h"

#define LOG_TAG "BKA_PI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

extern "C" {

extern s32 osSendMesg(OSMesgQueue *mq, OSMesg msg, s32 flag);
extern void ResourceMgr_HandleDma(void* dramAddr, u32 devAddr, u32 size);

// Synchronous ROM read — bypasses PI message queues
void piMgr_read(void *vaddr, s32 devaddr, s32 size) {
    if (!vaddr || size <= 0) return;
    ResourceMgr_HandleDma(vaddr, devaddr, size);
}
extern uint8_t* gN64_ROM_Base;
extern uint8_t* gN64_RDRAM;

// -----------------------------------------------------------------------
// -----------------------------------------------------------------------
s32 osPiRawStartDma(s32 direction, u32 devAddr, void *dramAddr, u32 size) {
    LOGI("osPiRawStartDma: dir=%d devAddr=0x%08X dramAddr=%p size=%u",
         direction, devAddr, dramAddr, size);
    if (direction == 0) { // OS_READ
        piMgr_read(dramAddr, devAddr, size);
    }
    return 0;
}

s32 osEPiRawStartDma(OSPiHandle *handle, s32 direction, u32 devAddr, void *dramAddr, u32 size) {
    return osPiRawStartDma(direction, devAddr, dramAddr, size);
}

s32 osPiStartDma(OSIoMesg *mb, s32 priority, s32 direction,
                 u32 devAddr, void *dramAddr, u32 size, OSMesgQueue *mq) {
    osPiRawStartDma(direction, devAddr, dramAddr, size);
    if (mq) osSendMesg(mq, (OSMesg)mb, 0);
    return 0;
}

s32 osEPiStartDma(OSPiHandle *handle, OSIoMesg *mb, s32 direction) {
    if (mb && direction == 0) {
        ResourceMgr_HandleDma(mb->dramAddr, mb->devAddr, mb->size);
        if (mb->hdr.retQueue) osSendMesg(mb->hdr.retQueue, (OSMesg)mb, 0);
    }
    return 0;
}

s32 osPiGetStatus(void) { return 0; }

} // extern "C"
