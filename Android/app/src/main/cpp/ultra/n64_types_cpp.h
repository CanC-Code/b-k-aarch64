#pragma once
// Minimal N64 type definitions for C++ bridge files
// Does NOT include ultra64.h to avoid C++ standard library conflicts

#include <stdint.h>
#include <stddef.h>

typedef uint8_t   u8;
typedef uint16_t  u16;
typedef uint32_t  u32;
typedef uint64_t  u64;
typedef int8_t    s8;
typedef int16_t   s16;
typedef int32_t   s32;
typedef int64_t   s64;
typedef float     f32;
typedef double    f64;
typedef int       n64_bool;

#define TRUE 1
#define FALSE 0

// Forward declarations for key N64 types used in bridge
struct OSMesgQueue_s;
typedef struct OSMesgQueue_s OSMesgQueue;
typedef void* OSMesg;
typedef u32 OSIntMask;
typedef u64 OSTime;
typedef u32 OSId;
typedef s32 OSPri;
