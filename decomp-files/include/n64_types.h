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
#define _ULTRATYPES_H_

// 3. Audio Library (AL) Basic Types
typedef s32           ALMicroTime;
typedef s32           ALPan;
typedef void* ALDMAproc;
typedef void* ALDMANew;

typedef struct ALHeap_s { uint8_t d[32]; } ALHeap;
typedef struct ALLink_s { struct ALLink_s *next; struct ALLink_s *prev; } ALLink;
typedef struct { uint8_t d[32]; } ALSynConfig;
typedef struct { uint8_t d[64]; } ALSynth;
typedef struct { uint8_t d[32]; } ALPlayer;
typedef struct { uint8_t d[32]; } ALWaveTable;
typedef struct { uint8_t d[32]; } ALRawLoop;
typedef struct { uint8_t d[32]; } ALSeqFile;
typedef struct { uint8_t d[32]; } ALInstrument;
typedef struct { uint8_t d[32]; } ALSound;
typedef struct { uint8_t d[64]; } ALCSPlayer;

// 4. Audio Processing States
typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int16_t POLEF_STATE[4];
typedef int16_t ENVMIX_STATE[40];

// 5. System Stubs
typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;
typedef struct { uint8_t d[128]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;

// 6. Graphics & ABI
typedef uint64_t Gfx;
typedef struct { unsigned int w0, w1; } Acmd_words;
typedef union { Acmd_words words; long long align; } Acmd;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[16]; } Vtx;

// 7. Virtualization Macros
#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

#endif
