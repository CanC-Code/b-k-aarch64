/* linker_stubs.c — provides symbols for N64 functions without including
 * any N64 headers, avoiding type conflicts. All functions are weak stubs
 * using generic pointer types. */

#include <stdint.h>
typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int32_t  s32;
typedef float    f32;
typedef uint64_t u64;
typedef int      n64_bool;

// Audio library
void alBnkfNew(void *f, void *table) {}
void alCSPSetBank(void *seqp, void *b) {}
void alCSPStop(void *seqp) {}
void alCSPSetSeq(void *seqp, void *seq) {}
void alCSPPlay(void *seqp) {}
void alCSPSetVol(void *seqp, s32 vol) { (void)vol; }
void alCSPSetTempo(void *seqp, s32 tempo) { (void)tempo; }
s32  alCSeqGetTicks(void *seq) { return 0; }
s32  alCSPGetTempo(void *seqp) { return 0; }
void alHeapInit(void *hp, void *base, s32 len) {}
void *alHeapDBAlloc(void *file, s32 line, void *hp, s32 num, s32 size) { return 0; }
void alLink(void *element, void *after) {}
void alUnlink(void *element) {}
void alEvtqNew(void *evtq, void *items, s32 itemCount) {}

// OS
void osInitialize(void) {}
u64  osGetTime(void) { return 0; }
u32  osViClock(void) { return 0; }
u32  osVirtualToPhysical(void *vaddr) { return (u32)(unsigned long)vaddr; }

// Graphics
void guMtxIdentF(void *mf) {}
void guMtxF2L(void *mf, void *m) {}
