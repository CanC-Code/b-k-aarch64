import os
import re
from pathlib import Path

BRIDGE_CONTENT = """
#ifndef _N64_TYPES_H_
#define _N64_TYPES_H_

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

typedef int8_t   s8;  typedef uint8_t  u8;
typedef int16_t  s16; typedef uint16_t u16;
typedef int32_t  s32; typedef uint32_t u32;
typedef int64_t  s64; typedef uint64_t u64;
typedef float    f32; typedef double   f64;
typedef volatile uint32_t vu32;
typedef u32 OSIntMask;

#ifndef TRUE
  #define TRUE 1
  #define FALSE 0
#endif

// Block legacy SDK headers
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

// System & Graphics
typedef uint64_t Gfx;
typedef struct { int32_t m[4][4]; } Mtx;
typedef struct { float m[4][4]; } MtxF;
typedef struct { uint8_t d[16]; } Vtx;

typedef void* OSMesg;
typedef struct { void* mt; void* full; int count; } OSMesgQueue;
typedef struct { uint8_t d[256]; } OSThread;
typedef struct { uint8_t d[64];  } OSContPad;

typedef struct { unsigned int w0, w1; } Acmd_words;
typedef union { Acmd_words words; long long force_align; } Acmd;

// DMA & Memory Heap
typedef s32 (*ALDMAproc)(s32 addr, s32 len, void *state);
typedef ALDMAproc (*ALDMANew)(void **state);

typedef struct { u8 *base; u8 *cur; u32 len; s32 count; } ALHeap;
typedef s32 ALMicroTime;
typedef s32 ALPan;
typedef struct { s16 maxVVoices; s16 maxPVoices; s16 maxUpdates; s16 maxFXbusses; void* dmaproc; ALHeap* heap; s32 fxType; s32 outputRate; void* params; } ALSynConfig;
typedef struct ALLink_s { struct ALLink_s *next; struct ALLink_s *prev; } ALLink;

typedef int16_t ADPCM_STATE[16];
typedef int16_t RESAMPLE_STATE[16];
typedef int16_t POLEF_STATE[4];
typedef int16_t ENVMIX_STATE[40];

// Audio Wave & Bank Data
typedef struct { uint8_t d[128]; } ALADPCMBook;
typedef struct { uint32_t start, end, count; ADPCM_STATE state; } ALADPCMloop;
typedef struct { uint32_t start, end, count; } ALRawLoop;

typedef struct ALWaveTable_s {
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

// Sequencer & MIDI Data
typedef struct { u8 *offset; s32 len; } ALSeqData;
typedef struct { s16 seqCount; ALSeqData seqArray[1]; } ALSeqFile;
typedef struct { u32 division; s32 trackOffset[16]; } ALCMidiHdr;

typedef struct {
    ALCMidiHdr *base; u32 validTracks; u32 lastDeltaTicks; u32 lastTicks; u32 deltaFlag;
    f32 qnpt; u8 *curLoc[16]; u8 *curBUPtr[16]; u32 curBULen[16]; u8 lastStatus[16]; u32 evtDeltaTicks[16];
} ALCSeq;

typedef struct {
    u32 validTracks; u32 lastTicks; u32 lastDeltaTicks; u8 *curLoc[16]; u8 *curBUPtr[16]; u32 curBULen[16]; u8 lastStatus[16]; u32 evtDeltaTicks[16];
} ALCSeqMarker;

typedef struct {
    s16 type; s32 ticks;
    union {
        struct { u8 status, byte1, byte2, duration; s32 ticks; } midi;
        struct { u8 status, type, byte1, byte2, byte3; s32 ticks; } tempo;
        struct { void *seq; } spseq;
        struct { void *bank; } spbank;
        struct { s16 vol; } spvol;
        struct { void *data; u32 unk0, unk4; } unk18;
        s32 i;
    } msg;
} ALEvent;

typedef struct ALEventListItem_s {
    struct ALEventListItem_s *next; struct ALEventListItem_s *prev; ALEvent evt;
} ALEventListItem;

typedef struct {
    ALEventListItem *allocList; ALEventListItem *freeList;
    s32 eventCount; s32 maxEventCount; ALMicroTime curTime;
    OSMesgQueue msgQ; OSMesg msg;
} ALEventQueue;

typedef struct { u8 pad[10]; u8 unkA; u8 pad2[21]; } N_ALChanState;

typedef struct {
    void *evtq; N_ALChanState *chanState; ALCSeq *target; ALMicroTime uspt; uint8_t padding[256];
} ALCSPlayer;

typedef struct {
    ALLink head; s16 numVoices; s16 curVol; s16 curPan; s16 curPitch;
    void *auxBus; void *mainBus; void *filterList;
    void *pFreeList; void *pAllocList; void *pLameList; void *paramList;
    uint8_t pad[256];
} ALSynth;

typedef struct ALVoice_s {
    ALLink node; struct PVoice_s *pvoice; ALWaveTable *table; void *clientPrivate;
    s16 state; s16 priority; s16 fxBus; s16 pan;
} ALVoice;

typedef struct {
    void* pvoice; ALWaveTable *table; void *clientPrivate;
    s16 state; s16 priority; s16 fxBus; s16 pan; ALSound *sound; 
} ALVoiceState;

typedef ALCSPlayer ALSeqPlayer;
typedef ALCSPlayer N_ALSeqPlayer;
typedef ALCSPlayer N_ALCSPlayer;
typedef ALSynth N_ALSynth;

typedef struct { N_ALSynth drvr; } ALGlobals_t;
extern ALGlobals_t *alGlobals;

// --- Constants & Macros (RESTORED) ---
#define OS_IM_NONE 0

// Hardware ADPCM
#define ADPCMFBYTES 9
#define LFSAMPLES 4
#define ADPCMFSIZE 16
#define AL_BANK_VERSION 0x424c
#define AL_ADPCM_WAVE 0
#define AL_RAW16_WAVE 1
#define UNITY_PITCH 0x8000

// RSP ABI Audio Commands
#define A_INIT 1
#define A_CONTINUE 0
#define A_RATE 0
#define A_VOL 1
#define A_LEFT 2
#define A_RIGHT 0
#define A_MAIN 0
#define A_AUX 2
#define A_LOOP 2
#define A_LOADBUFF 2
#define A_ADPCM 1

#define AL_MAIN_L_OUT 0
#define AL_MAIN_R_OUT 0
#define AL_AUX_L_OUT 0
#define AL_AUX_R_OUT 0

// Audio Driver States & Effects
#define AL_STOPPED 0
#define AL_PLAYING 1
#define AL_FX_SMALLROOM 0
#define AL_FX_BIGROOM 1
#define AL_FX_ECHO 2
#define AL_FX_CHORUS 3
#define AL_FX_FLANGE 4
#define AL_FX_CUSTOM 5

// Core Engine Event IDs
#define AL_SEQ_MIDI_EVT 1
#define AL_SEQP_MIDI_EVT 2
#define AL_TEMPO_EVT 5
#define AL_SEQ_END_EVT 6
#define AL_SEQP_SEQ_EVT 7
#define AL_SEQP_PLAY_EVT 8
#define AL_SEQP_BANK_EVT 9
#define AL_SEQP_STOPPING_EVT 10
#define AL_SEQP_VOL_EVT 11
#define AL_SEQP_META_EVT 12
#define AL_CSP_LOOPSTART 13
#define AL_CSP_LOOPEND 14
#define AL_UNK18_EVT 18

// Compressed MIDI Markers
#define AL_CMIDI_BLOCK_CODE 0xFE
#define AL_CMIDI_LOOPSTART_CODE 0x2E
#define AL_CMIDI_LOOPEND_CODE 0x2D

// Raw MIDI Command Parsing
#define AL_MIDI_NoteOff 0x80
#define AL_MIDI_NoteOn 0x90
#define AL_MIDI_PolyKeyPressure 0xA0
#define AL_MIDI_ControlChange 0xB0
#define AL_MIDI_ChannelModeSelect 0xB0
#define AL_MIDI_ProgramChange 0xC0
#define AL_MIDI_ChannelPressure 0xD0
#define AL_MIDI_PitchBendChange 0xE0
#define AL_MIDI_Meta 0xFF

#define AL_TRACK_END 0x2F
#define AL_MIDI_META_TEMPO 0x51
#define AL_MIDI_META_EOT 0x2F

#define K0_TO_PHYS(x) ((u32)(uintptr_t)(x))
static inline uint32_t osVirtualToPhysical(void* vaddr) { return (u32)(uintptr_t)vaddr; }

#endif
"""

def deploy_unabridged_bridge():
    root = Path.cwd().resolve()
    decomp = root / "decomp-files"
    include_dir = decomp / "include"
    
    print("--- [v118.0] DEPLOYING UNABRIDGED BRIDGE ---")
    
    bridge_path = include_dir / "n64_types.h"
    bridge_path.write_text(BRIDGE_CONTENT)

    toxic = [
        "2.0L/PR/os.h", "2.0L/PR/gbi.h", "2.0L/PR/abi.h", "2.0L/PR/mbi.h", 
        "2.0L/PR/gu.h", "2.0L/PR/sp.h", "2.0L/PR/ultratypes.h", 
        "2.0L/PR/libaudio.h", "2.0L/PR/n_libaudio.h", "2.0L/PR/R4300.h", "bool.h"
    ]
    for h in toxic:
        p = include_dir / h
        if p.exists():
            p.write_text("/* Terminated by v118.0 */\n")
    
    clash_types = [
        "MtxF", "Mtx", "Vtx", "ALEvent", "ALCSeq", "ALCSPlayer", "ALCSeqMarker", 
        "ALHeap", "ALWaveTable", "ALSynth", "ALEventQueue", "ALEventListItem", 
        "ALVoice", "ALVoiceState", "ALSeqPlayer"
    ]

    for path in decomp.rglob("*.[ch]"):
        if path.name == "n64_types.h": continue
        try:
            content = path.read_text(errors='ignore')
            original = content

            for ct in clash_types:
                content = re.sub(r'typedef\s+struct\s*[a-zA-Z0-9_]*\s*\{[^}]*\}\s*' + ct + r'\s*;', f'/* Terminated {ct} */', content)

            content = content.replace("typedef int bool;", "/* Terminated */")
            content = content.replace("typedef char bool;", "/* Terminated */")
            
            content = content.replace("evt.midi", "evt.msg.midi")
            content = content.replace("evt.unk18", "evt.msg.unk18")
            
            content = re.sub(r'\(u32\)\s*(&?\w+(?:->|\.)?\w*)', r'(u32)(uintptr_t)\1', content)

            if content != original:
                path.write_text(content)
        except: continue
        
    print("--- Unabridged Bridge Deployed. Execute Build Sequence. ---")

if __name__ == "__main__":
    deploy_unabridged_bridge()
