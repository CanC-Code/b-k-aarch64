#pragma once
// Minimal N64 OS types for C++ bridge files
// Does NOT pull in PR/gu.h, PR/libaudio.h, or any graphics headers

#include "n64_types_cpp.h"

// Thread
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

// Message
typedef void* OSMesg;

typedef struct OSMesgQueue_s {
    OSThread *mtqueue;
    OSThread *fullqueue;
    s32 validCount;
    s32 first;
    s32 msgCount;
    OSMesg *msg;
} OSMesgQueue;

// Task (simplified)
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

// PI
typedef struct OSPiHandle_s OSPiHandle;

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

// Controller
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

// EEPROM stubs
#define EEPROM_MAXBLOCKS 64
#define EEPROM_BLOCK_SIZE 8
