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

// 2. SDK Guards (Complete Lockout)
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

// 3. IO & Messaging (Fixes code_1D00.c)
typedef void* OSMesg;
typedef struct { void* mtqueue; void* fullqueue; s32 validCount; s32 first; s32 msgCount; OSMesg* msg; } OSMesgQueue;
typedef struct { uint8_t d[32]; } OSIoMesg; // Missing type restored
typedef s32  OSHWIntr;
#define OS_MESG_BLOCK 1
#define OS_TV_NTSC    0
extern s32 osTvType;

// 4. Graphics Pipe (GBI/RDP) Constants (Fixes code_15B30.c)
#define G_RM_NOOP           0
#define G_RM_NOOP2          0
#define G_ZBUFFER           0x00000001
#define G_SHADE             0x00000004
#define G_CULL_BOTH         0x00003000
#define G_FOG               0x00010000
#define G_LIGHTING          0x00020000
#define G_TEXTURE_GEN       0x00040000
#define G_TEXTURE_GEN_LINEAR 0x00080000
#define G_LOD               0x00100000
#define G_SHADING_SMOOTH    0x00200000
#define G_PM_NPRIMITIVE     0
#define G_AC_NONE           0
#define G_CD_MAGICSQ        0
#define G_SC_NON_INTERLACE  0
#define G_IM_FMT_RGBA       0
#define G_IM_SIZ_16b        1
#define G_CYC_1CYCLE        0
#define G_TC_FILT           0

// 5. Audio Pipeline & States
#define ADPCMFSIZE 16
#define UNITY_PITCH 0x8000
typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int16_t POLEF_STATE[4];
typedef int16_t ENVMIX_STATE[40];

// 6. Common Types & Structs
typedef uint64_t Gfx;
typedef uint64_t Acmd;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { uint8_t d[64]; } PositionalLight;

// 7. Dummy SDK Functions (Forwarding to nothing)
#define gDPSetRenderMode(p, m, m2) 
#define gSPClearGeometryMode(p, m)
#define gSPSetGeometryMode(p, m)
#define gSPTexture(p, s, t, l, f, d)

#ifndef bcopy
  #define bcopy(src, dst, n) __builtin_memmove(dst, src, n)
#endif

#endif
