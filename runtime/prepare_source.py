import os
import re
from pathlib import Path

# Note: We do NOT block _SCHED_H_ anymore, so Android's <sched.h> can load.
BRIDGE_CONTENT = """
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

// 1. Primitive Types
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar;
typedef volatile uint32_t vu32;

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

// 2. Hardware and Audio Types 
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { uint8_t d[16]; } Vtx;

typedef struct { float d[16]; } BoneTransform;
typedef struct { BoneTransform *transforms; int count; } BoneTransformList;
typedef void* VLA;
typedef void* FLA;
typedef struct { u32 t[16]; } OSTask_t;
typedef void (*OSErrorHandler)(void);
typedef struct { u32 d[16]; } OSLog;
typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;

// FIXED: OSThread now matches what exceptasm.cpp expects
typedef struct OSThread_s {
    struct OSThread_s *next;
    s32 priority;
    struct { u32 status; u32 d[63]; } context;
    uint8_t d[192]; 
} OSThread;

typedef struct { uint8_t d[64];  } OSContPad;

typedef struct { unsigned int w0, w1; } Acmd_words;
typedef union { Acmd_words words; long long force_align; } Acmd;
typedef s32 (*ALDMAproc)(s32 addr, s32 len, void *state);
typedef ALDMAproc (*ALDMANew)(void **state);
typedef struct { u8 *base; u8 *cur; u32 len; s32 count; } ALHeap;
typedef s32 ALMicroTime;
typedef s32 ALPan;

typedef struct ALLink_s { struct ALLink_s *next; struct ALLink_s *prev; void* (*handler)(void*); void* clientData; } ALLink;
typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int16_t POLEF_STATE[4];
typedef int16_t ENVMIX_STATE[40];

typedef struct { s32 order; s32 npredictors; s16 book[1]; } ALADPCMBook;
typedef struct { uint32_t start, end, count; ADPCM_STATE state; } ALADPCMloop;
typedef struct { uint32_t start, end, count; } ALRawLoop;

typedef struct ALWaveTable_s {
    union {
        struct { ALADPCMBook *book; ALADPCMloop *loop; } adpcmWave;
        struct { ALRawLoop *loop; } rawWave;
    } waveInfo;
    u8 *base; u32 len; u8 type, flags;
} ALWaveTable;

typedef struct { ALMicroTime attackTime; ALMicroTime decayTime; ALMicroTime releaseTime; u8 attackVolume; u8 decayVolume; } ALEnvelope;
typedef struct { u8 velocityMin; u8 velocityMax; u8 keyMin; u8 keyMax; u8 keyBase; s8 detune; } ALKeyMap;
typedef struct { s16 priority; s16 fxBus; u8 unityPitch; } ALVoiceConfig;

typedef struct { ALWaveTable *wavetable; u8 flags; ALEnvelope *envelope; ALKeyMap *keyMap; } ALSound;
typedef struct { s16 soundCount; u8 flags; u8 tremType; u8 tremRate; u8 tremDepth; u8 tremDelay; u8 vibType; u8 vibRate; u8 vibDepth; u8 vibDelay; ALSound *soundArray[1]; } ALInstrument;
typedef struct { u8 flags; s32 instCount; ALInstrument *percussion; ALInstrument *instArray[1]; } ALBank;
typedef struct { s16 revision; s32 bankCount; ALBank *bankArray[1]; } ALBankFile;

typedef struct { u8 *offset; s32 len; } ALSeqData;
typedef struct { s16 seqCount; ALSeqData seqArray[1]; } ALSeqFile;
typedef struct { u32 division; s32 trackOffset[16]; } ALCMidiHdr;

typedef struct { ALCMidiHdr *base; u32 validTracks; u32 lastDeltaTicks; u32 lastTicks; u32 deltaFlag; f32 qnpt; u8 *curLoc[16]; u8 *curBUPtr[16]; u32 curBULen[16]; u8 lastStatus[16]; u32 evtDeltaTicks[16]; } ALCSeq;
typedef ALCSeq ALSeq;
typedef struct { u32 validTracks; u32 lastTicks; u32 lastDeltaTicks; u8 *curLoc[16]; u8 *curBUPtr[16]; u32 curBULen[16]; u8 lastStatus[16]; u32 evtDeltaTicks[16]; } ALCSeqMarker;
typedef ALCSeqMarker ALSeqMarker;

struct ALVoiceState_s;
typedef struct { u8 status, byte1, byte2, duration; s32 ticks; } ALMIDIEvent;
typedef struct { u8 status, type, byte1, byte2, byte3; s32 ticks; u32 len; } ALTempoEvent;

typedef struct {
    s16 type; s32 ticks;
    union {
        ALMIDIEvent midi; ALTempoEvent tempo;
        struct { void *seq; } spseq; struct { void *bank; } spbank; struct { s16 vol; } spvol;
        struct { s16 vol; void* voice; s32 delta; } vol; struct { void* voice; } note;
        struct { struct ALVoiceState_s *vs; void* oscState; u8 chan; } osc;
        struct { u8 chan; u8 priority; } sppriority; struct { void* loop; } loop;
        struct { void *data; u32 unk0, unk4; } unk18; s32 i;
    } msg;
} ALEvent;

typedef struct ALEventListItem_s { ALLink node; ALMicroTime delta; ALEvent evt; } ALEventListItem;
typedef ALEventListItem N_ALEventListItem;
typedef struct { ALLink allocList; ALLink freeList; s32 eventCount; s32 maxEventCount; ALMicroTime curTime; OSMesgQueue msgQ; OSMesg msg; } ALEventQueue;
typedef struct { ALInstrument *instrument; s16 bendRange; u16 vol; u8 pan; u8 priority; u8 fxmix; u8 sustain; u8 unkA; u8 unkB; f32 pitchBend; u16 pad; } ALChanState;
typedef ALChanState N_ALChanState;

typedef struct ALVoice_s { ALLink node; struct PVoice_s *pvoice; ALWaveTable *table; void *clientPrivate; s16 state; s16 priority; s16 fxBus; s16 pan; } ALVoice;
typedef ALVoice N_ALVoice;

typedef struct ALVoiceState_s {
    struct ALVoiceState_s *next; ALVoice voice; ALWaveTable *table; void *clientPrivate;
    s16 state; s16 priority; s
