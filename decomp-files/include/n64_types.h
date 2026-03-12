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
#define _BOOL_H_ 

// 3. The "Acmd" Structure
typedef struct { unsigned int w0; unsigned int w1; } Acmd_words;
typedef union { Acmd_words words; long long force_align; } Acmd;

// 4. OS Stubs & Macros
typedef s32  OSPri;
typedef s32  OSId;
typedef void* OSMesg;
typedef s32  OSHWIntr;
typedef struct { void* mtqueue; void* fullqueue; s32 validCount; s32 first; s32 msgCount; OSMesg* msg; } OSMesgQueue;
typedef struct { uint8_t d[128]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;
typedef struct { uint8_t d[128]; } OSPfs;
typedef struct { uint8_t d[32];  } OSIoMesg;

#define OS_IM_NONE 0
typedef u32 OSIntMask;
#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline u32 osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

// 5. Audio/Video Constants
#define ADPCMFSIZE      16
#define UNITY_PITCH     0x8000
#define OS_TV_NTSC      0
extern s32 osTvType;

// 6. Graphics Types
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[16];  } Vtx; // RESTORED VTX
typedef struct { uint8_t d[32];  } LookAt;
typedef struct { uint8_t d[32];  } Hilite;
typedef struct { uint8_t d[32];  } Light;
typedef struct { uint8_t d[64];  } PositionalLight;

typedef int16_t ADPCM_STATE[16];

#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif
#endif
