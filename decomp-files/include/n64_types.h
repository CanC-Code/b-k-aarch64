#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

// 1. Basic Primitives
typedef uint8_t u8;   typedef int8_t s8;
typedef uint16_t u16; typedef int16_t s16;
typedef uint32_t u32; typedef int32_t s32;
typedef uint64_t u64; typedef int64_t s64;
typedef float f32;    typedef double f64;
typedef volatile uint32_t vu32;

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

// 2. SDK Guards
#define __OS_THREAD_H__
#define __OS_MESSAGE_H__
#define __OS_CONT_H__
#define _GBI_H_
#define _MBI_H_
#define _ABI_H_
#define _GU_H_
#define _BOOL_H_

// 3. The "Acmd" Structure (Fixes n_abi.h errors)
typedef struct {
    unsigned int w0;
    unsigned int w1;
} Acmd_words;

typedef union {
    Acmd_words words;
    long long  force_structure_alignment;
} Acmd;

// 4. OS Stubs & Macros
typedef s32  OSPri;
typedef s32  OSId;
typedef void* OSMesg;
typedef struct { uint8_t d[48];  } OSMesgQueue;
typedef struct { uint8_t d[128]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;

#define OS_IM_NONE 0
typedef u32 OSIntMask;
#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline u32 osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }
static inline OSIntMask osGetIntMask(void) { return 0; }
static inline OSIntMask osSetIntMask(OSIntMask m) { (void)m; return 0; }

// 5. Audio Pipeline Constants
#define ADPCMFSIZE      16
#define ADPCMVSIZE      8
#define LFSAMPLES       4
#define A_INIT          0x01
#define A_CONTINUE      0x02
#define A_LOOP          0x02
#define A_MAIN          0x04
#define A_AUX           0x08
#define A_VOL           0x10
#define A_RATE          0x20
#define A_LEFT          0x40
#define A_RIGHT         0x80
#define A_LOADBUFF      0x01
#define A_ADPCM         0x02

// 6. Graphics & Helper Types
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[16];  } Vtx;
typedef struct { uint8_t d[32];  } LookAt;
typedef struct { uint8_t d[32];  } Hilite;
typedef struct { uint8_t d[32];  } Light;
typedef struct { uint8_t d[64];  } PositionalLight;

typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int16_t POLEF_STATE[4];
typedef int16_t ENVMIX_STATE[40];

// N64 bit-shifting helpers
#define _SHIFTL(v, s, w) ((unsigned int)(((unsigned int)(v) & ((0x01 << (w)) - 1)) << (s)))
#define _SHIFTR(v, s, w) ((unsigned int)(((unsigned int)(v) >> (s)) & ((0x01 << (w)) - 1)))

#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif
#endif
