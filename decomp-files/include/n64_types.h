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

// 2. Global SDK Blockers
#define _GBI_H_
#define _ABI_H_
#define _MBI_H_
#define _LIBAUDIO_H_
#define _N_LIBAUDIO_H_
#define _GU_H_
#define _SP_H_
#define _ULTRATYPES_H_
#define __OS_H__
#define _MTXF_H_
#define _BOOL_H_

// 3. System & Graphics Core
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { uint8_t d[16]; } Vtx;

typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;
typedef struct { uint8_t d[256]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;

// 4. Audio Command Lists
typedef struct { unsigned int w0, w1; } Acmd_words;
typedef union { Acmd_words words; long long force_align; } Acmd;

// 5. Audio State Arrays & Primitives
typedef s32 ALMicroTime;
typedef s32 ALPan;
typedef void* ALDMAproc;
typedef void* ALDMANew;
typedef struct { uint8_t d[48]; } ALHeap;
typedef struct { uint8_t d[64]; } ALSynConfig;
typedef struct ALLink_s { struct ALLink_s *next; struct ALLink_s *prev; } ALLink;

typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int16_t POLEF_STATE[4];
typedef int16_t ENVMIX_STATE[40];

// 6. Audio Bank Blueprints (Rare/Banjo Layout)
typedef struct { uint8_t d[128]; } ALADPCMBook;
typedef struct { uint32_t start, end, count; ADPCM_STATE state; } ALADPCMloop;
typedef struct { uint32_t start, end, count; } ALRawLoop;

typedef struct {
    union {
        struct { ALADPCMBook *book; ALADPCMloop *loop; } adpcmWave;
        struct { ALRawLoop *loop; } rawWave;
    } waveInfo;
    u8 *base; u32 len; u8 type, flags;
} ALWaveTable;

typedef struct { uint8_t d[32]; } ALEnvelope;
typedef struct { uint8_t d[32]; } ALKeyMap;

typedef struct { ALWaveTable *wavetable; u8 flags; ALEnvelope *envelope; ALKeyMap *keyMap; } ALSound;
typedef struct { s16 soundCount; u8 flags; ALSound *soundArray[1]; } ALInstrument;
typedef struct { u8 flags; s32 instCount; ALInstrument *percussion; ALInstrument *instArray[1]; } ALBank;
typedef struct { s16 revision; s32 bankCount; ALBank *bankArray[1]; } ALBankFile;

typedef struct { u8 *offset; s32 len; } ALSeqData;
typedef struct { s16 seqCount; ALSeqData seqArray[1]; } ALSeqFile;

// 7. Sequencer Blueprints (MIDI Control)
typedef struct { u32 division; uint8_t d[28]; } ALCMidiHdr;
typedef struct { ALCMidiHdr *base; uint8_t d[256]; } ALCSeq;

typedef struct {
    s16 type;
    s32 ticks;
    union {
        struct { u8 status, byte1, byte2; s32 ticks; } midi;
        struct { u8 status, type, byte1, byte2, byte3; s32 ticks; } tempo;
        struct { void *seq; } spseq;
        struct { void *bank; } spbank;
        struct { void *data; u32 unk0, unk4; } unk18;
        s32 i;
    } msg;
} ALEvent;

typedef struct { u8 pad[10]; u8 unkA; u8 pad2[21]; } N_ALChanState;

typedef struct {
    void *evtq;
    N_ALChanState *chanState;
    ALMicroTime target;
    ALMicroTime uspt;
    uint8_t padding[256];
} ALCSPlayer;

typedef struct { uint8_t d[128]; } ALSynth;

// Rare 'N_' Aliases
typedef ALCSPlayer N_ALSeqPlayer;
typedef ALCSPlayer N_ALCSPlayer;
typedef ALSynth N_ALSynth;

// 8. Audio/MIDI Constants
#define AL_BANK_VERSION 0x424c
#define AL_ADPCM_WAVE 0
#define AL_RAW16_WAVE 1

#define AL_TRACK_END 0x2F
#define AL_MIDI_Meta 0xFF
#define AL_MIDI_META_TEMPO 0x51
#define AL_MIDI_META_EOT 0x2F

#define AL_SEQP_MIDI_EVT 2
#define AL_MIDI_ControlChange 3
#define AL_MIDI_ChannelModeSelect 4
#define AL_TEMPO_EVT 5
#define AL_SEQP_SEQ_EVT 6
#define AL_SEQP_PLAY_EVT 7
#define AL_SEQP_BANK_EVT 8
#define AL_UNK18_EVT 18

#define UNITY_PITCH 0x8000

#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

#endif
