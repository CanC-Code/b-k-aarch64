#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// 1. Basic N64 Primitives (64-bit Safe)
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

// 2. SDK Guards: Prevent any original header from loading
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
#define _SP_H_
#define _ULTRATYPES_H_

// 3. Command Lists (Acmd & Gfx)
typedef uint64_t Gfx;
typedef struct { unsigned int w0, w1; } Acmd_words;
typedef union { Acmd_words words; long long align; } Acmd;

// 4. Audio Emulation (AL) Structure Layouts
typedef s32 ALMicroTime;
typedef s32 ALPan;
typedef void* ALDMAproc;
typedef void* ALDMANew;
typedef struct { uint8_t d[32]; } ALHeap;
typedef struct ALLink_s { struct ALLink_s *next; struct ALLink_s *prev; } ALLink;

// Structures for sound banking
typedef struct { uint8_t d[32]; } ALADPCMBook;
typedef struct { uint8_t d[32]; } ALADPCMloop;
typedef struct { uint8_t d[32]; } ALRawLoop;

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
typedef struct { s32 instCount; ALSound *instArray[1]; } ALBank;
typedef struct { s32 bankCount; ALBank *bankArray[1]; } ALBankFile;
typedef struct { s16 seqCount; s32 seqArray[1]; } ALSeqFile;

// ALEvent Union (Fixes the midi/unk18 member errors)
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

// 5. System Stubs
typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;
typedef struct { uint8_t d[256]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;

// 6. Constants
#define OS_IM_NONE 0
#define ADPCMFSIZE 16
#define UNITY_PITCH 0x8000
#define AL_BANK_VERSION 0x424c // 'BL'
#define AL_SEQP_MIDI_EVT 2
#define AL_MIDI_ControlChange 3
#define AL_UNK18_EVT 18

static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }
#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

#endif
