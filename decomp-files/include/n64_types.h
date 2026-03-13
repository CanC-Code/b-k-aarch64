#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// 1. Basic N64 Primitives
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

// 2. SDK Lockdown Guards
#define _GBI_H_
#define _ABI_H_
#define _MBI_H_
#define _LIBAUDIO_H_
#define _N_LIBAUDIO_H_
#define _GU_H_
#define _SP_H_
#define _ULTRATYPES_H_
#define __OS_H__

// 3. Audio Command Union (The missing Acmd)
typedef struct { unsigned int w0, w1; } Acmd_words;
typedef union { Acmd_words words; long long force_align; } Acmd;

// 4. Detailed Audio Structure Mirroring
typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int16_t POLEF_STATE[4];
typedef int16_t ENVMIX_STATE[40];

typedef struct { uint8_t d[128]; } ALADPCMBook;
typedef struct { uint32_t start, end, count; int16_t state[16]; } ALADPCMloop;
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

typedef struct {
    u8 flags;
    s32 instCount; // Fixed: code_219D0.c needs this
    ALInstrument *percussion;
    ALInstrument *instArray[1];
} ALBank;

typedef struct {
    s16 revision; // Fixed: bnkf.c checks for AL_BANK_VERSION
    s32 bankCount;
    ALBank *bankArray[1];
} ALBankFile;

typedef struct { s16 seqCount; s32 seqArray[1]; } ALSeqFile;

// ALEvent Union (Rare/Banjo Layout)
typedef struct {
    s16 type;
    s32 ticks; // Fixed: code_21B50.c and code_21AF0.c need this
    union {
        struct { u8 status, byte1, byte2; } midi;
        struct { void *data; u32 unk0, unk4; } unk18;
        s32 i;
    } msg;
} ALEvent;

typedef struct { void *evtq; void *chanState; } ALCSPlayer;
typedef ALCSPlayer N_ALSeqPlayer;
typedef struct { uint8_t d[128]; } ALSynth;
typedef ALSynth N_ALSynth;

// 5. System, Graphics & Constants
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { uint8_t d[16]; } Vtx;

#define AL_BANK_VERSION 0x424c
#define AL_SEQP_MIDI_EVT 2
#define AL_UNK18_EVT 18
#define UNITY_PITCH 0x8000

typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;
typedef struct { uint8_t d[256]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;

#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

#endif
