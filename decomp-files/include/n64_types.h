#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// 1. Basic N64 Primitives (AArch64 Compatible)
typedef int8_t s8;   typedef uint8_t u8;
typedef int16_t s16; typedef uint16_t u16;
typedef int32_t s32; typedef uint32_t u32;
typedef int64_t s64; typedef uint64_t u64;
typedef float f32;   typedef double f64;
typedef volatile uint32_t vu32;

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

// 2. SDK Guards: Stop legacy headers in their tracks
#define _GBI_H_
#define _ABI_H_
#define _MBI_H_
#define _LIBAUDIO_H_
#define _N_LIBAUDIO_H_
#define _GU_H_
#define _SP_H_
#define _ULTRATYPES_H_
#define __OS_H__

// 3. Math & Graphics Structures
typedef struct { float m[4][4]; } MtxF;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[16]; } Vtx;
typedef uint64_t Gfx;

// 4. Command Lists (Audio/Graphics)
typedef struct { unsigned int w0, w1; } Acmd_words;
typedef union { Acmd_words words; long long force_align; } Acmd;

// 5. Audio Library (AL) Structures - Rare N_Audio Version
typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int16_t POLEF_STATE[4];
typedef int16_t ENVMIX_STATE[40];

typedef struct { uint32_t start, end, count; ADPCM_STATE state; } ALADPCMloop;
typedef struct { uint8_t d[128]; } ALADPCMBook;
typedef struct { uint32_t start, end, count; } ALRawLoop;

typedef struct {
    union {
        struct { ALADPCMBook *book; ALADPCMloop *loop; } adpcmWave;
        struct { ALRawLoop *loop; } rawWave;
    } waveInfo;
    u8 *base;
    u32 len;
    u8 type, flags;
} ALWaveTable;

typedef struct { ALWaveTable *wavetable; u8 flags; void* envelope; void* keyMap; } ALSound;
typedef struct { s32 instCount; ALSound *instArray[1]; } ALInstrument;
typedef struct { s32 instCount; ALSound *instArray[1]; } ALBank;
typedef struct { s32 bankCount; ALBank *bankArray[1]; } ALBankFile;
typedef struct { s16 seqCount; s32 seqArray[1]; } ALSeqFile;

typedef struct {
    s16 type;
    s32 ticks;
    union {
        struct { u8 status, byte1, byte2; } midi;
        struct { void *data; u32 unk0, unk4; } unk18;
        s32 i;
    } msg;
} ALEvent;

typedef struct { void *evtq; } ALCSPlayer;
typedef ALCSPlayer N_ALSeqPlayer;
typedef struct { uint8_t d[64]; } ALSynth;
typedef ALSynth N_ALSynth;

// 6. Audio Constants
#define AL_BANK_VERSION 0x424c
#define AL_ADPCM_WAVE 0
#define AL_RAW16_WAVE 1
#define AL_SEQP_MIDI_EVT 2
#define AL_MIDI_ControlChange 3
#define AL_MIDI_ChannelModeSelect 4
#define AL_UNK18_EVT 18
#define UNITY_PITCH 0x8000

// 7. System Stubs
typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;
typedef struct { uint8_t d[256]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;

// 8. Virtualization
#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }
#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

#endif
