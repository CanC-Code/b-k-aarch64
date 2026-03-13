#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// 1. Basic N64 Primitives
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef volatile uint32_t vu32;

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

// 2. SDK Guards: Stop the original SDK from ever running
#define __OS_H__
#define __OS_THREAD_H__
#define __OS_MESSAGE_H__
#define __OS_CONT_H__
#define _GBI_H_
#define _ABI_H_
#define _MBI_H_
#define _LIBAUDIO_H_
#define _N_LIBAUDIO_H_
#define _GU_H_
#define _ULTRATYPES_H_

// 3. Audio & Graphics State Buffers
typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int16_t POLEF_STATE[4];
typedef int16_t ENVMIX_STATE[40];

typedef struct { float m[4][4]; } MtxF;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[16]; } Vtx;
typedef uint64_t Gfx;

// 4. Detailed Audio Structure Emulation (N_Audio Version)
typedef s32 ALMicroTime;
typedef s32 ALPan;
typedef void* ALDMAproc;
typedef void* ALDMANew;
typedef struct { uint8_t d[32]; } ALHeap;
typedef struct ALLink_s { struct ALLink_s *next; struct ALLink_s *prev; } ALLink;

typedef struct { uint32_t start; uint32_t end; uint32_t count; ADPCM_STATE state; } ALADPCMloop;
typedef struct { uint32_t start; uint32_t end; uint32_t count; } ALRawLoop;

// Banjo-Kazooie specific flattened Event structure
typedef struct {
    s16 type;
    s32 ticks;
    union {
        struct { u8 status; u8 byte1; u8 byte2; } midi;
        struct { void *data; u32 unk0; u32 unk4; } unk18;
        s32 i;
    } msg;
} ALEvent;

typedef struct { void *evtq; } ALCSPlayer;
typedef struct { void *evtq; } N_ALSeqPlayer;
typedef struct { void *evtq; } N_ALCSPlayer;
typedef struct { uint8_t d[128]; } ALSynth;
typedef ALSynth N_ALSynth;

// 5. System Stubs
typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;
typedef struct { uint8_t d[256]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;

// 6. Constants used by Rare Audio
#define AL_SEQP_MIDI_EVT 2
#define AL_MIDI_ControlChange 3
#define AL_MIDI_ChannelModeSelect 4
#define AL_UNK18_EVT 18
#define UNITY_PITCH 0x8000

// 7. Virtualization
#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

#endif
