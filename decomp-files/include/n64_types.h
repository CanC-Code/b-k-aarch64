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
#define _GBI_H_
#define _MBI_H_
#define _ABI_H_
#define _GU_H_
#define _BOOL_H_ 

// 3. Audio Command Flags (The stubborn ones)
#ifndef A_LEFT
  #define A_LEFT      0x40
  #define A_RIGHT     0x80
  #define A_VOL       0x10
  #define A_RATE      0x20
  #define A_MAIN      0x04
  #define A_AUX       0x08
  #define A_INIT      0x01
  #define A_CONTINUE  0x02
#endif

// 4. OS Stubs & Messaging
typedef void* OSMesg;
typedef struct { void* mtqueue; void* fullqueue; s32 validCount; s32 first; s32 msgCount; OSMesg* msg; } OSMesgQueue;
typedef struct { uint8_t d[128]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;
typedef struct { uint8_t d[32];  } OSIoMesg;

#define OS_IM_NONE    0
#define OS_MESG_BLOCK 1
typedef u32 OSIntMask;
static inline u32 osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

// 5. Audio Pipeline Types
typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int16_t POLEF_STATE[4];
typedef int16_t ENVMIX_STATE[40];

// 6. Graphics & Common Types
typedef uint64_t Gfx;
typedef uint64_t Acmd;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[16];  } Vtx;

#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

#endif
