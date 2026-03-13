#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// 1. Basic Primitives (The Complete Set)
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef volatile uint32_t vu32;
typedef volatile uint8_t  vu8;

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

// 2. Total Eclipse Guards: Stop the original SDK from ever running
#define __OS_H__
#define __OS_THREAD_H__
#define __OS_MESSAGE_H__
#define __OS_CONT_H__
#define __OS_INTERNAL_H__
#define _OS_INTERNAL_EXCEPTION_H_ 
#define _GBI_H_
#define _MBI_H_
#define _ABI_H_
#define _GU_H_
#define _SP_H_
#define _BOOL_H_ 
#define _ULTRATYPES_H_

// 3. System Types
typedef void* OSMesg;
typedef struct { void* mtqueue; void* fullqueue; int validCount; } OSMesgQueue;
typedef struct { uint8_t d[128]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;
typedef struct { uint8_t d[32];  } OSIoMesg;
typedef s32 OSHWIntr;
typedef u32 OSIntMask;

// 4. Audio Pipeline
typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int16_t POLEF_STATE[4];
typedef int16_t ENVMIX_STATE[40];

#define ADPCMFSIZE 16
#define UNITY_PITCH 0x8000
#define A_INIT 1
#define A_MAIN 4
#define A_AUX 8

// 5. Graphics Pipeline (The "Redefinition" Fix)
// We define these as structs/longs to match AArch64 memory alignment
typedef uint64_t Gfx;
typedef struct { unsigned int w0; unsigned int w1; } Acmd_words;
typedef union { Acmd_words words; long long force_align; } Acmd;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[16]; } Vtx;
typedef struct { uint8_t d[32]; } Sprite;

// 6. Inline Stubs
#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

#endif
