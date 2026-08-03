#pragma once
// Comprehensive N64 OS types and constants for C++ bridge files
// Does NOT include ultra64.h or PR/ graphics headers

#include "n64_types_cpp.h"

#ifdef __cplusplus
extern "C" {
#endif

// --- Thread ---
typedef struct OSThread_s {
    struct OSThread_s *next;
    OSPri priority;
    struct OSThread_s **queue;
    struct OSThread_s *tlnext;
    u16 state;
    u16 flags;
    OSId id;
    int fp;
    long long int context[67];
} OSThread;

// --- Message ---
typedef void* OSMesg;

typedef struct OSMesgQueue_s {
    OSThread *mtqueue;
    OSThread *fullqueue;
    s32 validCount;
    s32 first;
    s32 msgCount;
    OSMesg *msg;
} OSMesgQueue;

typedef s32 OSEvent;

// --- Task ---
typedef struct {
    u32 type;
    u32 flags;
    void *ucode_boot;
    u32 ucode_boot_size;
    void *ucode;
    u32 ucode_size;
    void *ucode_data;
    u32 ucode_data_size;
    void *dram_stack;
    u32 dram_stack_size;
    void *output_buff;
    void *output_buff_size;
    void *data_ptr;
    u32 data_size;
    void *yield_data_ptr;
    u32 yield_data_size;
} OSTask_t;

typedef union {
    OSTask_t t;
    long long force_align;
} OSTask;

typedef s32 OSYieldResult;

// --- PI ---
typedef struct OSPiHandle_s {
    struct OSPiHandle_s *next;
    u8 type;
    u8 latency;
    u8 pageSize;
    u8 relDuration;
    u8 pulse;
    u8 domain;
    u32 baseAddress;
    u32 speed;
    long long transferInfo[16];
} OSPiHandle;

// --- IO ---
typedef struct {
    u16 type;
    u8 pri;
    OSMesgQueue *retQueue;
} OSMesgHdr;

typedef struct OSIoMesg_s {
    OSMesgHdr hdr;
    void *dramAddr;
    u32 devAddr;
    u32 size;
    OSPiHandle *piHandle;
} OSIoMesg;

// --- DevMgr ---
typedef struct OSDevMgr_s {
    s32 active;
    OSThread *thread;
    OSMesgQueue *cmdQueue;
    OSMesgQueue *evtQueue;
    OSMesgQueue *acsQueue;
    s32 (*dma)(s32, u32, void *, u32);
    s32 (*edma)(OSPiHandle *, s32, u32, void *, u32);
} OSDevMgr;

// --- VI ---
typedef struct OSViMode_s {
    u32 type;
    u32 comRegs[4];
    u32 fldRegs[2][7];
} OSViMode;

// --- Controller ---
typedef struct {
    u16 button;
    s8 stick_x;
    s8 stick_y;
    u8 errnum;
} OSContPad;

typedef struct {
    u16 type;
    u8 status;
    u8 errnum;
} OSContStatus;

// --- EEPROM ---
#define EEPROM_MAXBLOCKS 64
#define EEPROM_BLOCK_SIZE 8

// --- Constants ---
#define OS_MESG_NOBLOCK 0
#define OS_MESG_BLOCK 1
#define OS_READ 0
#define OS_WRITE 1

#define M_GFXTASK 1
#define M_AUDTASK 2
#define M_NULTASK 0

// --- PI Manager ---
void osCreatePiManager(OSPri pri, OSMesgQueue *cmdQ, OSMesg *cmdBuf, s32 cmdMsgCnt);

// --- DMA ---
s32 osPiRawStartDma(s32 direction, u32 devAddr, void *dramAddr, u32 size);

// --- AI ---
s32 osAiSetNextBuffer(void *bufPtr, u32 size);
u32 osAiGetLength(void);
s32 osAiSetFrequency(u32 frequency);

// --- EEPROM ---
s32 osEepromProbe(OSMesgQueue *mq);
s32 osEepromLongRead(OSMesgQueue *mq, u8 address, u8 *buffer, int nbytes);
s32 osEepromLongWrite(OSMesgQueue *mq, u8 address, u8 *buffer, int nbytes);
s32 osEepromRead(OSMesgQueue *mq, u8 address, u8 *buffer);
s32 osEepromWrite(OSMesgQueue *mq, u8 address, u8 *buffer);

#ifdef __cplusplus
}
#endif
