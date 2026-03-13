import os
import re
from pathlib import Path

# We define the types in a completely isolated block
BASIC_TYPES = """
#ifndef _BASIC_TYPES_H_
#define _BASIC_TYPES_H_
#include <stdint.h>
typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef uint8_t  uchar;
typedef volatile uint32_t vu32;
#ifndef _ULTRATYPES_H_
#define _ULTRATYPES_H_
#endif
#endif
"""

BRIDGE_CONTENT = """
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_
#include "basic_types.h"
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

#define _GBI_H_
#define _ABI_H_
#define _MBI_H_
#define _LIBAUDIO_H_
#define _N_LIBAUDIO_H_
#define _GU_H_
#define _SP_H_
#define __OS_H__
#define _MTXF_H_
#define _BOOL_H_
#define _SPTASK_H_
#define _REGION_H_
#define _RAMROM_H_
#define _RCP_H_

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
typedef struct { uint8_t d[256]; } OSThread;
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
    s16 state; s16 priority; s16 fxBus; s16 pan; ALSound *sound; 
    u8 flags; u8 envPhase; u8 phase; u8 channel; u8 velocity; ALMicroTime envEndTime; s16 envGain;
    u8 tremelo; f32 vibrato; f32 pitch;
} ALVoiceState;
typedef ALVoiceState N_ALVoiceState;

typedef struct ALFilter_s { struct ALFilter_s *source; void* (*handler)(struct ALFilter_s *filter, s16 *outp, s32 outLen, s32 sampleOffset, void *p); void (*setParam)(struct ALFilter_s *filter, s32 paramID, void *param); s16 type; s16 inp; s16 outp; s32 count; } ALFilter;
typedef ALFilter ALFx;

typedef struct { ALFilter filter; s32 sourceCount; s32 maxSources; ALFilter **sources; } ALMainBus;
typedef struct { ALFilter filter; s32 sourceCount; s32 maxSources; ALFilter **sources; ALFx *fx; } ALAuxBus;

typedef struct { ALLink head; s16 numVoices; s16 curVol; s16 curPan; s16 curPitch; ALAuxBus *auxBus; ALMainBus *mainBus; void *filterList; void *pFreeList; void *pAllocList; void *pLameList; void *paramList; uint8_t pad[256]; } ALSynth;
typedef struct N_ALFilter_s { struct N_ALFilter_s *source; void* (*handler)(s32 sampleOffset, struct N_ALFilter_s *filter); s16 type; s16 inp; s16 outp; s32 count; } N_ALFilter;
typedef struct { N_ALFilter filter; s32 sourceCount; s32 maxSources; N_ALFilter **sources; } N_ALMainBus;
typedef struct { ALLink head; s16 numVoices; s16 curVol; s16 curPan; s16 curPitch; ALAuxBus *auxBus; N_ALMainBus *mainBus; void *filterList; void *pFreeList; void *pAllocList; void *pLameList; void *paramList; s32 outputRate; void* sv_dramout; uint8_t pad[256]; } N_ALSynth;

typedef struct { s32 maxVoices; s32 maxEvents; u8 maxChannels; u8 debugFlags; ALHeap *heap; void* (*initOsc)(void**, f32*, u8, u8, u8, u8); ALMicroTime (*updateOsc)(void*, f32*); void (*stopOsc)(void*); } ALSeqpConfig;
typedef struct { s16 maxVVoices; s16 maxPVoices; s16 maxUpdates; s16 maxFXbusses; void* dmaproc; ALHeap* heap; s32 fxType; s32 outputRate; void* params; } ALSynConfig;

typedef struct {
    ALLink node; ALEvent nextEvent; ALEventQueue evtq; ALChanState *chanState; 
    ALSeq *target; ALMicroTime uspt; ALBank *bank; ALSynth *drvr;
    u32 chanMask; ALMicroTime nextDelta; s32 state; u16 vol;
    u8 maxChannels; u8 debugFlags; ALMicroTime frameTime; ALMicroTime curTime;
    void* (*initOsc)(void**, f32*, u8, u8, u8, u8);
    ALMicroTime (*updateOsc)(void*, f32*); void (*stopOsc)(void*);
    ALVoiceState *vFreeList; ALVoiceState *vAllocHead; ALVoiceState *vAllocTail;
    void* loopStart; void* loopEnd; s32 loopCount; uint8_t padding[64];
} ALCSPlayer;

typedef ALCSPlayer ALSeqPlayer;
typedef ALCSPlayer N_ALSeqPlayer;
typedef ALCSPlayer N_ALCSPlayer;
typedef ALEvent N_ALEvent;
typedef struct { N_ALSynth drvr; } ALGlobals;
extern ALGlobals *alGlobals;

#ifndef _SYNTHINTERNALS_H_
  #define AL_FILTER_ADD_SOURCE 1
  #define AL_RESAMPLE 1
  #define AL_ADPCM 2
#endif

#define AL_ADPCM_WAVE 0
#define AL_RAW16_WAVE 1
#define AL_BANK_VERSION 0x424c
#define ERR_ALBNKFNEW 0
#define AL_SEQP_MIDI_EVT 2
#define AL_UNK18_EVT 18
#define AL_MIDI_ControlChange 0xB0
#define AL_MIDI_ChannelModeSelect 0xB0
#define AL_EVTQ_END 0x7FFFFFFF
#define AL_USEC_PER_FRAME 16667
#define AL_PHASE_ATTACK 0
#define AL_PHASE_DECAY 1
#define AL_PHASE_SUSTAIN 2
#define AL_PHASE_RELEASE 3
#define AL_PHASE_NOTEON 4
#define AL_PHASE_SUSTREL 5
#define AL_STOPPED 0
#define AL_PLAYING 1
#define AL_STOPPING 2

#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }
#endif
"""

def deploy_loop_breaker():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v141.0] DEPLOYING LOOP BREAKER ---")
    
    # 1. Write Sacred Basic Types
    (include_dir / "basic_types.h").write_text(BASIC_TYPES)
    
    # 2. Write Master Bridge
    (include_dir / "n64_types.h").write_text(BRIDGE_CONTENT)

    # 3. Aggressively inject types into the problematic headers
    for target in ["model.h", "structs.h", "string.h", "rarezip.h"]:
        p = include_dir / target
        if p.exists():
            content = p.read_text(errors='ignore')
            # Move basic_types.h to the absolute top of the file
            content = "#include \"basic_types.h\"\\n" + content
            p.write_text(content)

    # 4. Clean up toxicity
    toxic = ["2.0L/PR/os.h", "2.0L/PR/ultratypes.h", "2.0L/PR/rcp.h", "2.0L/PR/ultraerror.h", "bool.h"]
    for h in toxic:
        p = include_dir / h
        if p.exists():
            p.write_text("/* Blocked */\\n")

    print("--- Loop Breaker Deployed. Run Ninja. ---")

if __name__ == "__main__":
    deploy_loop_breaker()
