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

// 2. Total Eclipse Guards
#define __OS_H__
#define __OS_THREAD_H__
#define __OS_MESSAGE_H__
#define __OS_CONT_H__
#define _GBI_H_
#define _MBI_H_
#define _ABI_H_
#define _GU_H_
#define _SP_H_
#define _ULTRATYPES_H_

// 3. Audio Library (AL) Structure Emulation
typedef struct { s16 seqCount; s32 seqArray[1]; } ALSeqFile;
typedef struct { u8 type; u8 flags; u8 *base; u32 len; } ALWaveTable;
typedef struct { uint8_t d[32]; } ALEnvelope;
typedef struct { uint8_t d[32]; } ALKeyMap;
typedef struct { uint8_t d[32]; } ALInstrument;
typedef struct { uint8_t d[32]; } ALSound;
typedef struct { uint8_t d[32]; } ALADPCMBook;
typedef struct { uint8_t d[32]; } ALADPCMloop;
typedef struct { uint8_t d[32]; } ALRawLoop;

typedef struct { 
    s16 type; 
    union { s32 i; void *ptr; } msg; 
} ALEvent;

typedef struct { void *evtq; uint8_t d[64]; } ALCSPlayer;
typedef ALCSPlayer N_ALSeqPlayer;
typedef struct { uint8_t d[64]; } ALSynth;
typedef ALSynth N_ALSynth;

#define AL_ADPCM_WAVE 0
#define AL_RAW16_WAVE 1
#define AL_SEQP_MIDI_EVT 2
#define AL_MIDI_ControlChange 3
#define AL_UNK18_EVT 18

// 4. Graphics Utility (GU) Types
typedef struct { uint8_t d[64]; } LookAt;
typedef struct { uint8_t d[64]; } Hilite;
typedef struct { uint8_t d[64]; } Light;
typedef struct { uint8_t d[64]; } PositionalLight;
typedef struct { uint8_t d[128]; } uSprite;
typedef struct { uint8_t d[128]; } Sprite;

// 5. System & Graphics ABI
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[16]; } Vtx;
typedef struct { unsigned int w0, w1; } Acmd_words;
typedef union { Acmd_words words; long long align; } Acmd;

typedef void* OSMesg;
typedef struct { void* mt; void* full; int validCount; } OSMesgQueue;
typedef struct { uint8_t d[128]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;

#define OS_IM_NONE 0
#define ADPCMFSIZE 16
#define UNITY_PITCH 0x8000

static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

#endif
