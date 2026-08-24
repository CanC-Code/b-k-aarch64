#pragma once
#include "n64_os_types_cpp.h"
#include <stdint.h>

// =======================================================================
// N64 F3DEX Display List → Software Rasterizer
//
// Intercepts Gfx tasks submitted via osSpTaskStartGo, parses the
// F3DEX command stream, and renders directly into gFramebuffers
// in RGB565 format.
//
// Thread safety: Must be called while holding the engine GIL.
// =======================================================================

#define DMEM_VERTEX_COUNT 64   // Max vertices in RSP DMEM
#define FB_WIDTH  292
#define FB_HEIGHT 216

// N64 Vertex format (16 bytes, same as original Vtx)
typedef struct {
    int16_t x, y, z;      // ob[3] - position (signed 16-bit)
    uint16_t flag;        // vertex flags
    int16_t s, t;         // tc[2] - texture coordinates (signed 16-bit)
    uint8_t r, g, b, a;   // cn[4] - color (unsigned 8-bit)
} BKVertex;

// 4x4 matrix (stored as float for transform)
typedef float BKMatrix[4][4];

// Gfx command (8 bytes, same as N64 Gfx)
typedef struct { uint32_t w0; uint32_t w1; uint32_t w2; uint32_t w3; } GfxCommand;
#define GFX_OPCODE(cmd) (((cmd).w0 >> 24) & 0xFF)

// RDP state (extended from original)
typedef struct {
    // Color state
    uint8_t primR, primG, primB, primA;
    uint8_t envR, envG, envB, envA;
    uint8_t blendR, blendG, blendB, blendA;
    uint8_t fillR, fillG, fillB, fillA;
    uint8_t fogR, fogG, fogB, fogA;
    
    // RDP modes
    uint32_t otherModeL, otherModeH;
    uint32_t combineMode;
    
    // Texture state
    uint8_t tmem[4096];
    uint8_t* texAddr;
    uint32_t texWidth, texFmt, texSize;
    int activeTile;
    int textureEnabled;
    
    // Tile descriptors (8 tiles)
    struct {
        uint32_t format, size, line, tmemAddr, palette;
        uint32_t clampT, mirrorT, maskT, shiftT;
        uint32_t clampS, mirrorS, maskS, shiftS;
        uint32_t sl, tl, sh, th;
    } tiles[8];
    
    // Matrix state
    BKMatrix projection;
    BKMatrix modelview;
    int matrixMode;  // 0=modelview, 1=projection

    // RSP segment base addresses (F3DEX_GBI)
    uintptr_t segmentBase[16];
    
    // DMEM vertex buffer
    BKVertex dmem[DMEM_VERTEX_COUNT];
    int dmemVertexCount;
} RDPState;

#ifdef __cplusplus
extern "C" {
#endif

void RSP_ProcessGfxTask(OSTask* tp);

#ifdef __cplusplus
}
#endif
