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

// 2. Total Eclipse Guards: Block original SDK headers
#define _GBI_H_
#define _ABI_H_
#define _MBI_H_
#define _LIBAUDIO_H_
#define _N_LIBAUDIO_H_
#define _ULTRATYPES_H_
#define __OS_H__

// 3. Audio & Graphics State Buffers
typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int16_t POLEF_STATE[4];
typedef int16_t ENVMIX_STATE[40];

typedef struct { float m[4][4]; } MtxF;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[16]; } Vtx;
typedef uint64_t Gfx;

// 4. Command Structures (Acmd)
typedef struct { unsigned int w0; unsigned int w1; } Acmd_words;
typedef union { Acmd_words words; long long force_align; } Acmd;

// 5. Audio Library (AL) Structures
typedef struct { uint8_t d[32]; } ALHeap;
typedef struct { uint8_t d[32]; } ALSynConfig;
typedef struct { s32 ticks; s32 type; union { s32 i; void *p; } msg; } ALEvent;
typedef s32 ALMicroTime;
typedef s32 ALPan;
typedef void* ALDMAproc;
typedef void* ALDMANew;
typedef struct ALLink_s { struct ALLink_s *next; struct ALLink_s *prev; } ALLink;

// 6. System Stubs
typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;
typedef struct { uint8_t d[128]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;

// 7. 64-bit Pointer Math Safety
#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

#endif
