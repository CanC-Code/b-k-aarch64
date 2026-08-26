#include "gfx_interpreter.h"
#include <android/log.h>
#include <cstring>
#include <cstdlib>
#include <cmath>
#include <algorithm>

#define LOG_TAG "BKA_GFX"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)

extern "C" {
    uint16_t gFramebuffers[2][FB_WIDTH * FB_HEIGHT];
    int getActiveFramebuffer(void);
    uint8_t* gN64_RDRAM;
    void* bka_lookup_addr_mapping(uint32_t key);
}

static RDPState s_rdp;

// Deterministic default segment bases (from decomp overlay layout)
// Populated before any RDP command runs, fixing many unmapped address errors.
static struct RDPStateDefaultSegments {
    RDPStateDefaultSegments() {
        s_rdp.segmentBase[0x01] = 0x80000000u;
        s_rdp.segmentBase[0x02] = 0x80000000u;
        s_rdp.segmentBase[0x03] = 0x80000000u;
        s_rdp.segmentBase[0x0C] = 0x0C000000u; // core2 overlay data (guessed)
    }
} s_rdpDefaultSegments;

static inline uint8_t* RDP_TranslateAddr(uint32_t addr) {
    if (addr == 0) return nullptr;

    // If osVirtualToPhysical stored this exact low-32 key, use the original
    // 64-bit host pointer first.
    void* p = bka_lookup_addr_mapping(addr);
    if (p) return (uint8_t*)p;

    // F3DEX_GBI segment address: top 4 bits select segment, lower 28 bits offset.
    // Only treat as segment if the address looks like a proper segmented address
    // (top nibble non-zero AND value below 0x10000000). Many low host pointers
    // start with 0x12..., 0x13..., etc., and must not be mistaken for segments.
    uint32_t seg = (addr >> 24) & 0x0F;
    uint32_t off = addr & 0x00FFFFFF;
    if (seg != 0 && addr < 0x10000000 && s_rdp.segmentBase[seg] != 0) {
        uint32_t base = s_rdp.segmentBase[seg];
        
        // 1. Try to resolve the base as a truncated host pointer FIRST
        void *base_pm = bka_lookup_addr_mapping(base);
        if (base_pm) {
            return (uint8_t*)base_pm + off;
        }
        
        // 2. Fallback: treat base + off as a combined N64 address
        uint32_t combined = base + off;
        void *pm = bka_lookup_addr_mapping(combined);
        if (pm) return (uint8_t*)pm;
        
        if (combined < 0x1000000u && gN64_RDRAM)
            return gN64_RDRAM + combined;
        if (combined >= 0x80000000u && combined < 0x81000000u && gN64_RDRAM)
            return gN64_RDRAM + (combined - 0x80000000u);
        if (combined >= 0xA0000000u && combined < 0xA1000000u && gN64_RDRAM)
            return gN64_RDRAM + (combined - 0xA0000000u);
            
        __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
            "RDP_TranslateAddr: segment %u unresolved base=0x%08X off=0x%08X",
            seg, base, off);
        return nullptr;
    }

    // Handle 0xFFxxxxxx as a 24-bit offset
    if ((addr & 0xFF000000u) == 0xFF000000u) {
        addr &= 0x00FFFFFFu;
    }

    // Handle 0x06xxxxxx-0x2FFFFFFF as custom virtual offsets.
    // These are either direct RDRAM offsets or custom banked addresses.
    if (addr >= 0x06000000u && addr < 0x30000000u) {
        addr &= 0x00FFFFFFu;
    }

    // Physical RDRAM.
    // Banjo-Kazooie uses custom virtual addresses. The actual RDRAM
    // offset is the lower 24 bits for these ranges:
    //   0x10xxxxxx, 0x18xxxxxx, 0x98xxxxxx-0x9Fxxxxxx
    if (((addr & 0xF0000000u) == 0x10000000u) ||
        ((addr & 0xFF000000u) >= 0x98000000u && (addr & 0xFF000000u) <= 0x9F000000u)) {
        addr &= 0x00FFFFFFu;
    }
    if (addr < 0x1000000u) {
        return gN64_RDRAM ? gN64_RDRAM + addr : nullptr;
    }
    if (addr >= 0x80000000u && addr < 0x81000000u) {
        return gN64_RDRAM ? gN64_RDRAM + (addr - 0x80000000u) : nullptr;
    }
    if (addr >= 0xA0000000u && addr < 0xA1000000u) {
        return gN64_RDRAM ? gN64_RDRAM + (addr - 0xA0000000u) : nullptr;
    }

    // No valid mapping found.
    __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
        "RDP_TranslateAddr: unmapped address 0x%08X", addr);
    return nullptr;
}

static int s_frameCount = 0;

// =======================================================================
// Helpers
// =======================================================================

static inline uint32_t RDP_BPP(uint32_t size) {
    static const uint32_t bpp[] = {0, 1, 2, 2};
    return bpp[size & 3];
}

static inline uint16_t RGBA8_TO_RGB565(uint8_t r, uint8_t g, uint8_t b) {
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
}

static inline int16_t read_int16(const uint8_t* ptr) {
    return (int16_t)((ptr[0] << 8) | ptr[1]);
}

// =======================================================================
// RDP State Management
// =======================================================================

static void RDP_InitState() {
    // Save vertex buffer across frames (RSP DMEM persists between tasks)
    static BKVertex saved_dmem[DMEM_VERTEX_COUNT];
    static int saved_dmemVertexCount = 0;
    memcpy(saved_dmem, s_rdp.dmem, sizeof(saved_dmem));
    saved_dmemVertexCount = s_rdp.dmemVertexCount;

    memset(&s_rdp, 0, sizeof(s_rdp));

    // Restore vertex buffer and count - CRITICAL: keep the count so triangles can find vertices
    memcpy(s_rdp.dmem, saved_dmem, sizeof(saved_dmem));
    s_rdp.dmemVertexCount = saved_dmemVertexCount;
    __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
        "RDP_InitState: restored dmemVertexCount=%d", saved_dmemVertexCount);

    s_rdp.primR = s_rdp.primG = s_rdp.primB = s_rdp.primA = 255;
    s_rdp.envR = s_rdp.envG = s_rdp.envB = s_rdp.envA = 255;
    s_rdp.blendR = s_rdp.blendG = s_rdp.blendB = 255; s_rdp.blendA = 255;
    s_rdp.fillR = s_rdp.fillG = s_rdp.fillB = 255; s_rdp.fillA = 255;
    s_rdp.fogR = s_rdp.fogG = s_rdp.fogB = 255; s_rdp.fogA = 255;
    s_rdp.activeTile = 0;
    s_rdp.textureEnabled = false;
    s_rdp.matrixMode = 0;
    // CRITICAL: Do NOT reset dmemVertexCount here - it was just restored above.
    // If set to 0, all triangle commands will fail bounds checks.
    
    // Initialize matrices to identity
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++)
            s_rdp.projection[i][j] = s_rdp.modelview[i][j] = (i == j) ? 1.0f : 0.0f;
}

// =======================================================================
// Matrix Operations
// =======================================================================

static void Matrix_Identity(BKMatrix m) {
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++)
            m[i][j] = (i == j) ? 1.0f : 0.0f;
}

static void Matrix_MultVec(const BKMatrix m, float x, float y, float z, float w,
                           float* ox, float* oy, float* oz, float* ow) {
    *ox = m[0][0]*x + m[0][1]*y + m[0][2]*z + m[0][3]*w;
    *oy = m[1][0]*x + m[1][1]*y + m[1][2]*z + m[1][3]*w;
    *oz = m[2][0]*x + m[2][1]*y + m[2][2]*z + m[2][3]*w;
    *ow = m[3][0]*x + m[3][1]*y + m[3][2]*z + m[3][3]*w;
}

// Load N64 fixed-point matrix (int16_t[4][4] with 32-bit integer parts)
static void Matrix_LoadFromN64(BKMatrix dst, const void* src) {
    const uint8_t* bytes = (const uint8_t*)src;
    // N64 F3DEX matrices are stored COLUMN-MAJOR (M[i][j] = column i, row j).
    // Our Matrix_MultVec expects ROW-MAJOR (m[row][col]).
    // So we transpose during load.
    for (int col = 0; col < 4; col++) {
        for (int row = 0; row < 4; row++) {
            // N64 matrix entries are 32-bit fixed-point (16.16), stored big-endian.
            uint32_t raw = ((uint32_t)bytes[0] << 24) |
                           ((uint32_t)bytes[1] << 16) |
                           ((uint32_t)bytes[2] << 8)  |
                           ((uint32_t)bytes[3]);
            bytes += 4;
            int32_t val = (int32_t)raw;
            dst[row][col] = (float)val / 65536.0f;
        }
    }
}

// =======================================================================
// Texture Fetch from TMEM
// =======================================================================

static void RDP_FetchTexel(int tile, uint32_t s, uint32_t t, uint8_t* outRGBA) {
    uint32_t u = s >> 5, v = t >> 5;
    auto& tdesc = s_rdp.tiles[tile];
    uint32_t bpp = RDP_BPP(tdesc.size);
    uint32_t texW = (tdesc.sh >> 2) + 1, texH = (tdesc.th >> 2) + 1;
    
    if (tdesc.clampS) { if (u >= texW) u = texW - 1; } else { u &= (texW - 1); }
    if (tdesc.clampT) { if (v >= texH) v = texH - 1; } else { v &= (texH - 1); }
    
    uint32_t tmemBase = tdesc.tmemAddr * 8, lineBytes = tdesc.line * 8;
    
    if (bpp == 2) {
        uint32_t offset = tmemBase + v * lineBytes + u * 2;
        if (offset + 1 < 4096) {
            uint16_t pixel = (s_rdp.tmem[offset] << 8) | s_rdp.tmem[offset + 1];
            if (tdesc.format == 0) {
                outRGBA[0] = ((pixel >> 11) & 0x1F) << 3;
                outRGBA[1] = ((pixel >> 6) & 0x1F) << 3;
                outRGBA[2] = ((pixel >> 1) & 0x1F) << 3;
                outRGBA[3] = (pixel & 1) ? 255 : 0;
            } else if (tdesc.format == 5) {
                outRGBA[0] = outRGBA[1] = outRGBA[2] = (pixel >> 8) & 0xFF;
                outRGBA[3] = pixel & 0xFF;
            } else {
                outRGBA[0] = outRGBA[1] = outRGBA[2] = outRGBA[3] = 255;
            }
        } else { outRGBA[0] = outRGBA[1] = outRGBA[2] = outRGBA[3] = 0; }
    } else if (bpp == 1) {
        uint32_t offset = tmemBase + v * lineBytes + u;
        if (offset < 4096) {
            uint8_t pixel = s_rdp.tmem[offset];
            if (tdesc.format == 4) {
                outRGBA[0] = outRGBA[1] = outRGBA[2] = (pixel & 0xF0);
                outRGBA[3] = (pixel & 0x0F) << 4;
            } else {
                outRGBA[0] = outRGBA[1] = outRGBA[2] = outRGBA[3] = pixel;
            }
        } else { outRGBA[0] = outRGBA[1] = outRGBA[2] = outRGBA[3] = 0; }
    } else {
        outRGBA[0] = outRGBA[1] = outRGBA[2] = outRGBA[3] = 255;
    }
}

// =======================================================================
// Triangle Rasterizer (flat shaded, no Z-buffer yet)
// =======================================================================

static int s_triangleCount = 0;

static void RasterizeTriangle(
    float x0, float y0, float x1, float y1, float x2, float y2,
    uint8_t r0, uint8_t g0, uint8_t b0, uint8_t a0,
    uint8_t r1, uint8_t g1, uint8_t b1, uint8_t a1,
    uint8_t r2, uint8_t g2, uint8_t b2, uint8_t a2)
{
    s_triangleCount++;
    if (s_triangleCount <= 10) {
        __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
            "RasterizeTriangle #%d: (%.1f,%.1f) (%.1f,%.1f) (%.1f,%.1f)",
            s_triangleCount, x0, y0, x1, y1, x2, y2);
    }
    // Sort vertices by Y (y0 <= y1 <= y2)
    if (y0 > y1) { std::swap(x0, x1); std::swap(y0, y1); std::swap(r0, r1); std::swap(g0, g1); std::swap(b0, b1); std::swap(a0, a1); }
    if (y1 > y2) { std::swap(x1, x2); std::swap(y1, y2); std::swap(r1, r2); std::swap(g1, g2); std::swap(b1, b2); std::swap(a1, a2); }
    if (y0 > y1) { std::swap(x0, x1); std::swap(y0, y1); std::swap(r0, r1); std::swap(g0, g1); std::swap(b0, b1); std::swap(a0, a1); }

    int iy0 = (int)ceilf(y0), iy1 = (int)ceilf(y1), iy2 = (int)ceilf(y2);
    if (iy0 < 0) iy0 = 0; if (iy2 > FB_HEIGHT) iy2 = FB_HEIGHT;
    if (iy0 >= iy2) return;

    int activeFb = getActiveFramebuffer();
    uint16_t* fb = gFramebuffers[activeFb];

    float dy10 = y1 - y0, dy21 = y2 - y1, dy20 = y2 - y0;
    float dx10 = x1 - x0, dx21 = x2 - x1, dx20 = x2 - x0;
    if (dy10 <= 0.0f && dy20 <= 0.0f) return;

    // Top half (y0 to y1)
    if (dy10 > 0.0f) {
        for (int y = iy0; y < iy1 && y < FB_HEIGHT; y++) {
            float fy = (float)y + 0.5f;
            float t0 = (fy - y0) / dy20;
            float t1 = (fy - y0) / dy10;
            
            float lx = x0 + t0 * dx20;
            float rx = x0 + t1 * dx10;
            if (lx > rx) std::swap(lx, rx);
            
            int ilx = (int)ceilf(lx), irx = (int)ceilf(rx);
            if (ilx < 0) ilx = 0; if (irx > FB_WIDTH) irx = FB_WIDTH;
            
            for (int x = ilx; x < irx; x++) {
                // Flat shading - use average color
                uint8_t r = (uint8_t)(((int)r0 + r1 + r2) / 3);
                uint8_t g = (uint8_t)(((int)g0 + g1 + g2) / 3);
                uint8_t b = (uint8_t)(((int)b0 + b1 + b2) / 3);
                fb[y * FB_WIDTH + x] = RGBA8_TO_RGB565(r, g, b);
            }
        }
    }
    
    // Bottom half (y1 to y2)
    if (dy21 > 0.0f) {
        for (int y = iy1; y < iy2 && y < FB_HEIGHT; y++) {
            float fy = (float)y + 0.5f;
            float t0 = (fy - y0) / dy20;
            float t1 = (fy - y1) / dy21;
            
            float lx = x0 + t0 * dx20;
            float rx = x1 + t1 * dx21;
            if (lx > rx) std::swap(lx, rx);
            
            int ilx = (int)ceilf(lx), irx = (int)ceilf(rx);
            if (ilx < 0) ilx = 0; if (irx > FB_WIDTH) irx = FB_WIDTH;
            
            for (int x = ilx; x < irx; x++) {
                uint8_t r = (uint8_t)(((int)r0 + r1 + r2) / 3);
                uint8_t g = (uint8_t)(((int)g0 + g1 + g2) / 3);
                uint8_t b = (uint8_t)(((int)b0 + b1 + b2) / 3);
                fb[y * FB_WIDTH + x] = RGBA8_TO_RGB565(r, g, b);
            }
        }
    }
}

// =======================================================================
// Vertex Transform: apply combined matrix + viewport
// =======================================================================

static void TransformVertex(const BKVertex* v, float* sx, float* sy) {
    float x = (float)v->x, y = (float)v->y, z = (float)v->z;
    
    // Apply modelview
    float ox, oy, oz, ow;
    Matrix_MultVec(s_rdp.modelview, x, y, z, 1.0f, &ox, &oy, &oz, &ow);
    
    // Apply projection
    Matrix_MultVec(s_rdp.projection, ox, oy, oz, ow, &ox, &oy, &oz, &ow);
    
    // Perspective divide
    if (fabsf(ow) > 0.0001f) {
        ox /= ow; oy /= ow;
    }
    
    // Viewport transform: NDC [-1,1] → screen [0,FB_WIDTH/HEIGHT]
    *sx = (ox + 1.0f) * 0.5f * (float)FB_WIDTH;
    *sy = (1.0f - oy) * 0.5f * (float)FB_HEIGHT;
}

// =======================================================================
// Command Handlers
// =======================================================================

static void Cmd_SetPrimColor(GfxCommand cmd) {
    s_rdp.primR = (cmd.w1 >> 24) & 0xFF;
    s_rdp.primG = (cmd.w1 >> 16) & 0xFF;
    s_rdp.primB = (cmd.w1 >> 8) & 0xFF;
    s_rdp.primA = cmd.w1 & 0xFF;
}

static void Cmd_SetEnvColor(GfxCommand cmd) {
    s_rdp.envR = (cmd.w1 >> 24) & 0xFF;
    s_rdp.envG = (cmd.w1 >> 16) & 0xFF;
    s_rdp.envB = (cmd.w1 >> 8) & 0xFF;
    s_rdp.envA = cmd.w1 & 0xFF;
}

static void Cmd_SetFillColor(GfxCommand cmd) {
    uint16_t c = cmd.w1 & 0xFFFF; // drawRectangle2D packs RGBA5551 into both halves
    s_rdp.fillR = ((c >> 11) & 0x1F) << 3;
    s_rdp.fillG = ((c >> 6) & 0x1F) << 3;
    s_rdp.fillB = ((c >> 1) & 0x1F) << 3;
    s_rdp.fillA = (c & 1) ? 255 : 0;
}

static void Cmd_SetOtherModeL(GfxCommand cmd) {
    uint32_t length = (cmd.w0 >> 8) & 0xFF, shift = cmd.w0 & 0xFF, data = cmd.w1;
    uint32_t mask = ((1 << (length + 1)) - 1) << shift;
    s_rdp.otherModeL = (s_rdp.otherModeL & ~mask) | ((data << shift) & mask);
}

static void Cmd_SetOtherModeH(GfxCommand cmd) {
    uint32_t length = (cmd.w0 >> 8) & 0xFF, shift = cmd.w0 & 0xFF, data = cmd.w1;
    uint32_t mask = ((1 << (length + 1)) - 1) << shift;
    s_rdp.otherModeH = (s_rdp.otherModeH & ~mask) | ((data << shift) & mask);
}

static void Cmd_SetCombine(GfxCommand cmd) {
    s_rdp.combineMode = (cmd.w0 & 0x00FFFFFF) | (cmd.w1 & 0xFF000000);
}

static void Cmd_Texture(GfxCommand cmd) {
    uint32_t enable = (cmd.w0 >> 16) & 0xFF, tile = (cmd.w0 >> 8) & 0xFF;
    s_rdp.textureEnabled = (enable != 0);
    if (tile < 8) s_rdp.activeTile = tile;
}

static void Cmd_SetTile(GfxCommand cmd) {
    uint32_t tile = (cmd.w1 >> 24) & 0x7;
    if (tile >= 8) return;
    auto& t = s_rdp.tiles[tile];
    t.format  = (cmd.w0 >> 21) & 0x7;
    t.size    = (cmd.w0 >> 19) & 0x3;
    t.line    = (cmd.w0 >> 9) & 0x1FF;
    t.tmemAddr = cmd.w0 & 0x1FF;
    t.palette = (cmd.w0 >> 20) & 0xF;
    t.clampT  = (cmd.w0 >> 18) & 0x1;
    t.mirrorT = (cmd.w0 >> 17) & 0x1;
    t.maskT   = (cmd.w0 >> 13) & 0xF;
    t.shiftT  = (cmd.w0 >> 9) & 0xF;
    t.clampS  = (cmd.w1 >> 31) & 0x1;
    t.mirrorS = (cmd.w1 >> 30) & 0x1;
    t.maskS   = (cmd.w1 >> 26) & 0xF;
    t.shiftS  = (cmd.w1 >> 22) & 0xF;
}

static void Cmd_SetTileSize(GfxCommand cmd) {
    uint32_t tile = (cmd.w1 >> 24) & 0x7;
    if (tile >= 8) return;
    auto& t = s_rdp.tiles[tile];
    t.sl = (cmd.w0 >> 12) & 0xFFF;
    t.tl = cmd.w0 & 0xFFF;
    t.sh = (cmd.w1 >> 12) & 0xFFF;
    t.th = cmd.w1 & 0xFFF;
}

static void Cmd_SetTImg(GfxCommand cmd) {
    s_rdp.texFmt  = (cmd.w0 >> 21) & 0x7;
    s_rdp.texSize = (cmd.w0 >> 19) & 0x3;
    s_rdp.texWidth = (cmd.w0 >> 9) & 0x3FF;
    s_rdp.texAddr = RDP_TranslateAddr(cmd.w1);
}

static void Cmd_LoadTile(GfxCommand cmd) {
    uint32_t tile = (cmd.w0 >> 24) & 0x7;
    if (tile >= 8) return;
    auto& t = s_rdp.tiles[tile];
    uint32_t sl = (cmd.w0 >> 12) & 0xFFF, tl = cmd.w0 & 0xFFF;
    uint32_t sh = (cmd.w1 >> 12) & 0xFFF, th = cmd.w1 & 0xFFF;
    t.sl = sl; t.tl = tl; t.sh = sh; t.th = th;
    
    uint32_t bpp = RDP_BPP(t.size);
    if (bpp == 0) bpp = 1;
    uint32_t texWidth = (sh >> 2) + 1, texHeight = (th >> 2) + 1;
    uint32_t texSize = texWidth * texHeight * bpp;
    uint32_t lineWords = (texWidth * bpp + 7) / 8;
    
    if (s_rdp.texAddr && texSize <= 4096) {
        uint32_t tmemBase = t.tmemAddr * 8;
        uint32_t srcLineStride = s_rdp.texWidth * bpp;
        for (uint32_t row = 0; row < texHeight; row++) {
            uint32_t srcOffset = (tl + row) * srcLineStride + sl * bpp;
            uint32_t dstOffset = tmemBase + row * lineWords * 8;
            if (dstOffset + lineWords * 8 <= 4096)
                memcpy(s_rdp.tmem + dstOffset, s_rdp.texAddr + srcOffset, lineWords * 8);
        }
        t.line = lineWords;
    }
}

static void Cmd_LoadTLUT(GfxCommand cmd) {
    uint32_t tile = (cmd.w0 >> 24) & 0x7;
    if (tile >= 8) return;
    auto& t = s_rdp.tiles[tile];
    uint32_t sl = (cmd.w0 >> 12) & 0xFFF;
    uint32_t tl = cmd.w0 & 0xFFF;
    uint32_t count = (cmd.w1 >> 14) & 0x3FF;
    if (s_rdp.texAddr) {
        uint32_t tmemBase = t.tmemAddr * 8;
        uint32_t srcOffset = tl * 2 + sl * 2;
        memcpy(s_rdp.tmem + tmemBase, s_rdp.texAddr + srcOffset, (count + 1) * 2);
    }
}

static void Cmd_LoadBlock(GfxCommand cmd) {
    uint32_t tile = (cmd.w0 >> 24) & 0x7;
    if (tile >= 8) return;
    auto& t = s_rdp.tiles[tile];
    uint32_t sl = (cmd.w0 >> 12) & 0xFFF, tl = cmd.w0 & 0xFFF;
    uint32_t sh = (cmd.w1 >> 12) & 0xFFF, th = cmd.w1 & 0xFFF;
    t.sl = sl; t.tl = tl; t.sh = sh; t.th = th;
    
    uint32_t bpp = RDP_BPP(t.size);
    if (bpp == 0) bpp = 1;
    uint32_t texWidth = (sh >> 2) + 1, texHeight = (th >> 2) + 1;
    uint32_t texSize = texWidth * texHeight * bpp;
    uint32_t lineWords = (texWidth * bpp + 7) / 8;
    
    if (s_rdp.texAddr && texSize <= 4096) {
        uint32_t tmemBase = t.tmemAddr * 8;
        for (uint32_t row = 0; row < texHeight; row++) {
            uint32_t srcOffset = row * lineWords * 8;
            uint32_t dstOffset = tmemBase + row * lineWords * 8;
            if (dstOffset + lineWords * 8 <= 4096)
                memcpy(s_rdp.tmem + dstOffset, s_rdp.texAddr + srcOffset, lineWords * 8);
        }
        t.line = lineWords;
    }
}

// =======================================================================
// G_VTX - Load vertices into DMEM (F3DEX_GBI format)
// w0 = [G_VTX:8][v0:8][n:6][length:10]
// w1 = address of Vtx data in RDRAM
// =======================================================================
static int s_vtxCallCount = 0;
static void Cmd_Vtx(GfxCommand cmd) {
    s_vtxCallCount++;
    __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
        "Cmd_Vtx CALL #%d: w0=0x%08X w1=0x%08X", s_vtxCallCount, cmd.w0, cmd.w1);
    uint32_t v0 = (cmd.w0 >> 16) & 0xFF; // Base vertex index in DMEM
    uint32_t n  = ((cmd.w0 >> 10) & 0x3F) + 1;  // F3DEX_GBI stores (count-1)
    uint32_t length = cmd.w0 & 0x3FF;           // Data length
    uint32_t addr = cmd.w1;                     // Source address
    
    
    
    if (v0 + n > DMEM_VERTEX_COUNT || !gN64_RDRAM) {
        LOGW("Cmd_Vtx: v0=%u n=%u exceeds DMEM limit", v0, n);
        return;
    }
    
    uint8_t* src = RDP_TranslateAddr(addr);
    if (!src) {
        LOGW("Cmd_Vtx: failed to translate addr=0x%08X", addr);
        return;
    }
    __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
        "Cmd_Vtx: loading v0=%u n=%u addr=0x%08X s_rdp.dmemVertexCount=%d",
        v0, n, addr, s_rdp.dmemVertexCount);
    for (uint32_t i = 0; i < n; i++) {
        BKVertex* v = &s_rdp.dmem[v0 + i];
        // N64 Vtx format (16 bytes): ob[3](6 bytes), flag(2), tc[2](4), cn[4](4)
        v->x = read_int16(src + 0);
        v->y = read_int16(src + 2);
        v->z = read_int16(src + 4);
        v->flag = (src[6] << 8) | src[7];
        v->s = read_int16(src + 8);
        v->t = read_int16(src + 10);
        v->r = src[12];
        v->g = src[13];
        v->b = src[14];
        v->a = src[15];
        src += 16;
    }
    
    if (v0 + n > (uint32_t)s_rdp.dmemVertexCount)
        s_rdp.dmemVertexCount = v0 + n;
    __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
        "Cmd_Vtx: loaded %u vertices, s_rdp.dmemVertexCount=%d", n, s_rdp.dmemVertexCount);
}

// =======================================================================
// G_TRI1 - Draw 1 triangle
// w0 = [G_TRI1:8][v2:8][v1:8][v0:8]
// w1 = [flag:24][00000000]
// =======================================================================

static void Cmd_Tri1(GfxCommand cmd) {
    uint32_t packed = cmd.w1;   // F3DEX_GBI: indices packed in w1, opcode only in w0
    uint32_t v0 = ((packed >> 16) & 0xFF) >> 1;
    uint32_t v1 = ((packed >> 8) & 0xFF) >> 1;
    uint32_t v2 = (packed & 0xFF) >> 1;

    if (v0 >= (uint32_t)s_rdp.dmemVertexCount ||
        v1 >= (uint32_t)s_rdp.dmemVertexCount ||
        v2 >= (uint32_t)s_rdp.dmemVertexCount) {
        __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
            "Cmd_Tri1: INVALID vertex indices %u,%u,%u (dmemVertexCount=%d)",
            v0, v1, v2, s_rdp.dmemVertexCount);
        return;
    }

    BKVertex* vert0 = &s_rdp.dmem[v0];
    BKVertex* vert1 = &s_rdp.dmem[v1];
    BKVertex* vert2 = &s_rdp.dmem[v2];

    float sx0, sy0, sx1, sy1, sx2, sy2;
    TransformVertex(vert0, &sx0, &sy0);
    TransformVertex(vert1, &sx1, &sy1);
    TransformVertex(vert2, &sx2, &sy2);

    RasterizeTriangle(sx0, sy0, sx1, sy1, sx2, sy2,
        vert0->r, vert0->g, vert0->b, vert0->a,
        vert1->r, vert1->g, vert1->b, vert1->a,
        vert2->r, vert2->g, vert2->b, vert2->a);
}

// =======================================================================
// G_TRI2 - Draw 2 triangles (4 vertices)
// w0 = [G_TRI2:8][v2:8][v1:8][v0:8]  -- triangle 1 uses v0,v1,v2
// w1 = [flag2:8][v4:8][v3:8][flag1:8]  -- triangle 2 uses v1,v2,v3
// =======================================================================

static void Cmd_Tri2(GfxCommand cmd) {
    uint32_t tri1 = cmd.w0 & 0xFFFFFF;  // first triangle packed in lower 24 bits
    uint32_t tri2 = cmd.w1;             // second triangle packed in w1

    uint32_t v00 = ((tri1 >> 16) & 0xFF) >> 1;
    uint32_t v01 = ((tri1 >> 8) & 0xFF) >> 1;
    uint32_t v02 = (tri1 & 0xFF) >> 1;
    uint32_t v10 = ((tri2 >> 16) & 0xFF) >> 1;
    uint32_t v11 = ((tri2 >> 8) & 0xFF) >> 1;
    uint32_t v12 = (tri2 & 0xFF) >> 1;

    if (v00 >= (uint32_t)s_rdp.dmemVertexCount ||
        v01 >= (uint32_t)s_rdp.dmemVertexCount ||
        v02 >= (uint32_t)s_rdp.dmemVertexCount ||
        v10 >= (uint32_t)s_rdp.dmemVertexCount ||
        v11 >= (uint32_t)s_rdp.dmemVertexCount ||
        v12 >= (uint32_t)s_rdp.dmemVertexCount) {
        __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
            "Cmd_Tri2: INVALID vertex indices %u,%u,%u,%u,%u,%u (dmemVertexCount=%d)",
            v00, v01, v02, v10, v11, v12, s_rdp.dmemVertexCount);
        return;
    }

    {
        BKVertex* vt0 = &s_rdp.dmem[v00];
        BKVertex* vt1 = &s_rdp.dmem[v01];
        BKVertex* vt2 = &s_rdp.dmem[v02];
        float sx0, sy0, sx1, sy1, sx2, sy2;
        TransformVertex(vt0, &sx0, &sy0);
        TransformVertex(vt1, &sx1, &sy1);
        TransformVertex(vt2, &sx2, &sy2);
        RasterizeTriangle(sx0, sy0, sx1, sy1, sx2, sy2,
            vt0->r, vt0->g, vt0->b, vt0->a,
            vt1->r, vt1->g, vt1->b, vt1->a,
            vt2->r, vt2->g, vt2->b, vt2->a);
    }

    {
        BKVertex* vt0 = &s_rdp.dmem[v10];
        BKVertex* vt1 = &s_rdp.dmem[v11];
        BKVertex* vt2 = &s_rdp.dmem[v12];
        float sx0, sy0, sx1, sy1, sx2, sy2;
        TransformVertex(vt0, &sx0, &sy0);
        TransformVertex(vt1, &sx1, &sy1);
        TransformVertex(vt2, &sx2, &sy2);
        RasterizeTriangle(sx0, sy0, sx1, sy1, sx2, sy2,
            vt0->r, vt0->g, vt0->b, vt0->a,
            vt1->r, vt1->g, vt1->b, vt1->a,
            vt2->r, vt2->g, vt2->b, vt2->a);
    }
}


// =======================================================================
// G_TRI1 (F3DEX2 variant, opcode 0xC4)
// w0 = [G_TRI1:8][v0:8][v1:8][v2:8]
// w1 = flag
// =======================================================================
static void Cmd_Tri1_F3DEX2(GfxCommand cmd) {
    uint32_t v0 = (cmd.w0 >> 17) & 0x7F;
    uint32_t v1 = (cmd.w0 >> 9) & 0x7F;
    uint32_t v2 = (cmd.w0 >> 1) & 0x7F;

    if (v0 >= (uint32_t)s_rdp.dmemVertexCount ||
        v1 >= (uint32_t)s_rdp.dmemVertexCount ||
        v2 >= (uint32_t)s_rdp.dmemVertexCount) {
        __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
            "Cmd_Tri1_F3DEX2: INVALID vertex indices %u,%u,%u (dmemVertexCount=%d)",
            v0, v1, v2, s_rdp.dmemVertexCount);
        return;
    }

    BKVertex* vert0 = &s_rdp.dmem[v0];
    BKVertex* vert1 = &s_rdp.dmem[v1];
    BKVertex* vert2 = &s_rdp.dmem[v2];

    float sx0, sy0, sx1, sy1, sx2, sy2;
    TransformVertex(vert0, &sx0, &sy0);
    TransformVertex(vert1, &sx1, &sy1);
    TransformVertex(vert2, &sx2, &sy2);

    RasterizeTriangle(sx0, sy0, sx1, sy1, sx2, sy2,
        vert0->r, vert0->g, vert0->b, vert0->a,
        vert1->r, vert1->g, vert1->b, vert1->a,
        vert2->r, vert2->g, vert2->b, vert2->a);
}

// =======================================================================
// G_TRI2 (F3DEX2 variant, opcode 0x34)
// w0 = [G_TRI2:8][v0:8][v1:8][v2:8]   (first triangle)
// w1 = [flag:8][v3:8][v4:8][v5:8]     (second triangle, flag ignored)
// =======================================================================
static void Cmd_Tri2_F3DEX2(GfxCommand cmd) {
    uint32_t v00 = (cmd.w0 >> 17) & 0x7F;
    uint32_t v01 = (cmd.w0 >> 9) & 0x7F;
    uint32_t v02 = (cmd.w0 >> 1) & 0x7F;
    uint32_t v10 = (cmd.w1 >> 17) & 0x7F;
    uint32_t v11 = (cmd.w1 >> 9) & 0x7F;
    uint32_t v12 = (cmd.w1 >> 1) & 0x7F;

    if (v00 >= (uint32_t)s_rdp.dmemVertexCount ||
        v01 >= (uint32_t)s_rdp.dmemVertexCount ||
        v02 >= (uint32_t)s_rdp.dmemVertexCount ||
        v10 >= (uint32_t)s_rdp.dmemVertexCount ||
        v11 >= (uint32_t)s_rdp.dmemVertexCount ||
        v12 >= (uint32_t)s_rdp.dmemVertexCount) {
        LOGW("Cmd_Tri2_F3DEX2: invalid vertex indices %u,%u,%u,%u,%u,%u",
             v00, v01, v02, v10, v11, v12);
        return;
    }

    {
        BKVertex* vt0 = &s_rdp.dmem[v00];
        BKVertex* vt1 = &s_rdp.dmem[v01];
        BKVertex* vt2 = &s_rdp.dmem[v02];
        float sx0, sy0, sx1, sy1, sx2, sy2;
        TransformVertex(vt0, &sx0, &sy0);
        TransformVertex(vt1, &sx1, &sy1);
        TransformVertex(vt2, &sx2, &sy2);
        RasterizeTriangle(sx0, sy0, sx1, sy1, sx2, sy2,
            vt0->r, vt0->g, vt0->b, vt0->a,
            vt1->r, vt1->g, vt1->b, vt1->a,
            vt2->r, vt2->g, vt2->b, vt2->a);
    }

    {
        BKVertex* vt0 = &s_rdp.dmem[v10];
        BKVertex* vt1 = &s_rdp.dmem[v11];
        BKVertex* vt2 = &s_rdp.dmem[v12];
        float sx0, sy0, sx1, sy1, sx2, sy2;
        TransformVertex(vt0, &sx0, &sy0);
        TransformVertex(vt1, &sx1, &sy1);
        TransformVertex(vt2, &sx2, &sy2);
        RasterizeTriangle(sx0, sy0, sx1, sy1, sx2, sy2,
            vt0->r, vt0->g, vt0->b, vt0->a,
            vt1->r, vt1->g, vt1->b, vt1->a,
            vt2->r, vt2->g, vt2->b, vt2->a);
    }
}

// =======================================================================
// G_MOVEMEM - Load matrix (opcode 0xDC)
// w0 = [opcode:8][length:8][offset:8][index:8]
// w1 = address of data in RDRAM
// =======================================================================
static void Cmd_MoveMem(GfxCommand cmd) {
    uint32_t length = (cmd.w0 >> 16) & 0xFF;
    uint32_t offset = (cmd.w0 >> 8) & 0xFF;
    uint32_t index  = cmd.w0 & 0xFF;
    uint32_t addr   = cmd.w1 & 0x0FFFFFFF;
    
    if (!gN64_RDRAM) return;
    
    // Matrix load: index 0x0E = G_MTX_MODELVIEW, 0x00 = G_MTX_PROJECTION
    // offset 0 = projection, offset 0 = modelview (upper bits differ)
    if (length == 8 && (index == 0x0E || index == 0x00)) {
        BKMatrix* target;
        // F3DEX2 G_MOVEMEM: index 0x0E = G_MTX_PROJECTION, 0x00 = G_MTX_MODELVIEW
        if (index == 0x0E) {
            target = &s_rdp.projection;
        } else {
            target = &s_rdp.modelview;
        }
        void *mtx_src = RDP_TranslateAddr(addr);
        if (mtx_src) Matrix_LoadFromN64(*target, mtx_src);
    }
}

// =======================================================================
// G_MTX - Load matrix (opcode 0xBC)
// F3DEX2 format: w0 = [G_MTX:8][flag:8][param:16], w1 = matrix address
// For our initial implementation, we treat the matrix as modelview.
// =======================================================================
static void Cmd_MoveWord(GfxCommand cmd) {
    uint32_t index = cmd.w0 & 0xFF;
    uint32_t offset = (cmd.w0 >> 8) & 0xFFFF;
    uint32_t data = cmd.w1;

    if (index == 0x06) { // G_MW_SEGMENT
        uint32_t segment = (offset / 4) & 0x0F;
        void *base_ptr = RDP_TranslateAddr(data);
        s_rdp.segmentBase[segment] = (uintptr_t)base_ptr;
        __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
            "Cmd_MoveWord SEGMENT seg=%u offset=0x%04X base=%p", segment, offset, base_ptr);
        // Banjo-Kazooie uses segments 4 and 12 for overlays that mirror segment 1
        if (segment == 1) {
            s_rdp.segmentBase[4] = (uintptr_t)base_ptr;
            s_rdp.segmentBase[12] = (uintptr_t)base_ptr;
        }
    }
}

// =======================================================================
// G_MTX - Load matrix (opcode 0x01)
// =======================================================================
static void Cmd_Mtx(GfxCommand cmd) {
    uint32_t flag = (cmd.w0 >> 16) & 0xFF;
    uint32_t raw_addr = cmd.w1;
    void *mtx_src = RDP_TranslateAddr(raw_addr);
    if (!mtx_src) return;
    
    // G_MTX flags: bit 0 = push, bit 1 = load (not used), bit 2 = projection
    // In F3DEX2: G_MTX_PROJECTION = 0x04, G_MTX_MODELVIEW = 0x00
    if (flag & 0x04) {
        Matrix_LoadFromN64(s_rdp.projection, mtx_src);
    } else {
        Matrix_LoadFromN64(s_rdp.modelview, mtx_src);
    }
}

// =======================================================================
// G_FILLRECT - Solid color rectangle fill
// =======================================================================
static void Cmd_FillRect(GfxCommand cmd) {
    int32_t ulx = (int32_t)((cmd.w1 >> 14) & 0x3FF);
    int32_t uly = (int32_t)((cmd.w1 >> 2) & 0x3FF);
    int32_t lrx = (int32_t)((cmd.w0 >> 14) & 0x3FF);
    int32_t lry = (int32_t)((cmd.w0 >> 2) & 0x3FF);
    
    ulx >>= 2; uly >>= 2; lrx >>= 2; lry >>= 2;
    ulx = std::max(0, ulx); uly = std::max(0, uly);
    lrx = std::min(lrx, FB_WIDTH); lry = std::min(lry, FB_HEIGHT);
    if (ulx >= lrx || uly >= lry) return;
    
    uint16_t color = RGBA8_TO_RGB565(s_rdp.fillR, s_rdp.fillG, s_rdp.fillB);
    int activeFb = getActiveFramebuffer();
    uint16_t* fb = gFramebuffers[activeFb];
    for (int32_t y = uly; y < lry; y++)
        for (int32_t x = ulx; x < lrx; x++)
            fb[y * FB_WIDTH + x] = color;
}

// =======================================================================
// G_TEXRECT - Textured rectangle
// =======================================================================
static void Cmd_TexRect(GfxCommand cmd) {
    int32_t xh = (int32_t)((cmd.w0 >> 12) & 0xFFF);
    int32_t yh = (int32_t)(cmd.w0 & 0xFFF);
    int32_t xl = (int32_t)((cmd.w1 >> 12) & 0xFFF);
    int32_t yl = (int32_t)(cmd.w1 & 0xFFF);
    int tile = (cmd.w1 >> 24) & 0x7;
    
    xl >>= 2; yl >>= 2; xh >>= 2; yh >>= 2;
    if (xl < 0) xl = 0; if (yl < 0) yl = 0;
    if (xh > FB_WIDTH) xh = FB_WIDTH; if (yh > FB_HEIGHT) yh = FB_HEIGHT;
    if (xl >= xh || yl >= yh) return;
    if (tile < 0 || tile >= 8) return;
    
    auto& tdesc = s_rdp.tiles[tile];
    int32_t texW = (tdesc.sh >> 2) + 1, texH = (tdesc.th >> 2) + 1;
    if (texW <= 0) texW = 1; if (texH <= 0) texH = 1;
    
    int32_t rectW = xh - xl, rectH = yh - yl;
    if (rectW <= 0 || rectH <= 0) return;
    
    int32_t sBase = (tdesc.sl >> 5), tBase = (tdesc.tl >> 5);
    int activeFb = getActiveFramebuffer();
    uint16_t* fb = gFramebuffers[activeFb];
    uint8_t texel[4];
    
    for (int32_t dy = 0; dy < rectH; dy++) {
        for (int32_t dx = 0; dx < rectW; dx++) {
            int32_t s = sBase + (dx * texW) / rectW;
            int32_t t = tBase + (dy * texH) / rectH;
            RDP_FetchTexel(tile, s << 5, t << 5, texel);
            
            uint8_t r = (uint8_t)(((uint16_t)texel[0] * s_rdp.primR) / 255);
            uint8_t g = (uint8_t)(((uint16_t)texel[1] * s_rdp.primG) / 255);
            uint8_t b = (uint8_t)(((uint16_t)texel[2] * s_rdp.primB) / 255);
            uint8_t a = (uint8_t)(((uint16_t)texel[3] * s_rdp.primA) / 255);
            if (a < 8) continue;
            
            int32_t px = xl + dx, py = yl + dy;
            if (px >= 0 && px < FB_WIDTH && py >= 0 && py < FB_HEIGHT)
                fb[py * FB_WIDTH + px] = RGBA8_TO_RGB565(r, g, b);
        }
    }
}

// =======================================================================
// G_DL - Jump to display list
// =======================================================================
static void Cmd_DL(GfxCommand cmd, GfxCommand** outCmd, size_t* outRemaining) {
    uint32_t addr = cmd.w1;
    *outCmd = (GfxCommand*)RDP_TranslateAddr(addr);
    *outRemaining = 0xFFFFFFFF;
}

static void* RSP_ResolveGfxAddress(uint32_t addr) {
    uint32_t seg = (addr >> 28) & 0x0F;
    uint32_t offset = addr & 0x0FFFFFFF;
    if (seg != 0 && seg < 16 && s_rdp.segmentBase[seg] != 0) {
        return (uint8_t*)s_rdp.segmentBase[seg] + offset;
    }
    return RDP_TranslateAddr(addr);
}

// =======================================================================
// Main Dispatch
// =======================================================================

static int s_rspCallCount = 0;
void RSP_ProcessGfxTask(OSTask* tp) {
    s_rspCallCount++;
    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
        "RSP_ProcessGfxTask CALL #%d: tp=%p type=%d data=%p size=%u dmemVertexCount=%d",
        s_rspCallCount, tp, tp ? tp->t.type : -1, tp ? tp->t.data_ptr : nullptr,
        tp ? tp->t.data_size : 0, s_rdp.dmemVertexCount);

    if (!tp || !tp->t.data_ptr || tp->t.data_size == 0) {
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "early return: tp=%p data=%p size=%u",
            tp, tp ? tp->t.data_ptr : nullptr, tp ? tp->t.data_size : 0);
        return;
    }

    {
        const unsigned char *p = (const unsigned char*)tp->t.data_ptr;
        __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
            "data bytes: %02x %02x %02x %02x %02x %02x %02x %02x  %02x %02x %02x %02x %02x %02x %02x %02x",
            p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7],
            p[8], p[9], p[10], p[11], p[12], p[13], p[14], p[15]);
    }

    RDP_InitState();

    // Only clear framebuffers on first call (static flag)
    static bool s_firstFrame = true;
    if (s_firstFrame) {
        memset(gFramebuffers[0], 0, sizeof(gFramebuffers[0]));
        memset(gFramebuffers[1], 0, sizeof(gFramebuffers[1]));
        s_firstFrame = false;
        __android_log_print(ANDROID_LOG_INFO, "BKA_GFX", "Framebuffers cleared (first frame)");
    }

    struct DListFrame {
        uint8_t *ptr;
        uint8_t *end;
    };

    DListFrame stack[64];
    int depth = 0;
    size_t current_stride = 16;
    size_t stack_stride[64];
    uint8_t *cur = (uint8_t*)tp->t.data_ptr;
    uint8_t *cur_end = cur + tp->t.data_size;

    const size_t MAX_TOTAL_CMDS = 20000;
    const size_t MAX_DL_CMDS = 5000;
    size_t total = 0;
    size_t dl_cmds = 0;
    int zero_run = 0;

    while (cur + current_stride <= cur_end) {
        if (++total > MAX_TOTAL_CMDS) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "runaway display list: exceeded %u total commands", (unsigned)MAX_TOTAL_CMDS);
            break;
        }
        if (++dl_cmds > MAX_DL_CMDS) {
            __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                "runaway display list: exceeded %u commands in current DL", (unsigned)MAX_DL_CMDS);
            break;
        }

        GfxCommand c = {0};
        memcpy(&c, cur, 16);
        uint8_t opcode = GFX_OPCODE(c);

        if (s_frameCount <= 3) {
            __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
                "cmd[%zu] depth=%d op=0x%02X w0=0x%08X w1=0x%08X",
                total - 1, depth, opcode, c.w0, c.w1);
        }

        cur += current_stride;

        if (c.w0 == 0 && c.w1 == 0) {
            zero_run++;
            if (zero_run >= 16) {
                if (depth > 0) {
                    // Dump the bytes after zero padding to inspect for hidden geometry
                    const uint8_t* after = cur;
                    __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
                        "zero-run pop at cmd %zu, depth=%d next_bytes=%02x %02x %02x %02x %02x %02x %02x %02x",
                        total - 1, depth, after[0], after[1], after[2], after[3],
                        after[4], after[5], after[6], after[7]);
                    depth--;
                    cur = stack[depth].ptr;
                    cur_end = stack[depth].end;
                    current_stride = stack_stride[depth];
                    dl_cmds = 0;
                    zero_run = 0;
                    continue;
                } else {
                    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                        "zero-run break at cmd %zu, depth=%d", total - 1, depth);
                    break;
                }
            }
        } else {
            zero_run = 0;
        }

        // Nested display lists in Banjo-Kazooie often omit ENDDL and are
        // followed by vertex/index data. We now use the task data size
        // as the boundary, so no early stop is needed.

                switch (opcode) {
            case 0x00:
            case 0xC0:
            case 0xE8:
            case 0xE7:
            case 0xE9:
            case 0xE6:
            case 0xE1:
            case 0xF1:
            case 0xF0:
            case 0x02:
            case 0xDB:
            case 0xDA:
            case 0xBD:
            case 0xBE:
            case 0xBB:
            case 0xBA:
            case 0xB9:
            case 0xB7:
            case 0xB6:
            case 0xED:
            case 0xFF:
                break;

            case 0xF7: Cmd_SetFillColor(c); break;
            case 0xFA: Cmd_SetPrimColor(c); break;
            case 0xFB: Cmd_SetEnvColor(c); break;
            case 0xE2: Cmd_SetOtherModeL(c); break;
            case 0xE3: Cmd_SetOtherModeH(c); break;
            case 0xFC: Cmd_SetCombine(c); break;
            case 0xD7: Cmd_Texture(c); break;
            case 0xF5: Cmd_SetTile(c); break;
            case 0xF2: Cmd_SetTileSize(c); break;
            case 0xFD: Cmd_SetTImg(c); break;
            case 0xF3: Cmd_LoadBlock(c); break;
            case 0xF4: Cmd_LoadTile(c); break;
            case 0xF6: Cmd_FillRect(c); break;
            case 0xE4: case 0xE5: Cmd_TexRect(c); break;

            case 0x01: Cmd_Mtx(c); break;
            case 0x04: Cmd_Vtx(c); break;
            case 0xBF: __android_log_print(ANDROID_LOG_INFO, "BKA_GFX", "TRI dispatch 0xBF w1=0x%08X", c.w1); Cmd_Tri1(c); break;
            case 0xC4: __android_log_print(ANDROID_LOG_INFO, "BKA_GFX", "TRI dispatch 0xC4 w0=0x%08X", c.w0); Cmd_Tri2_F3DEX2(c); break;
            case 0x34: __android_log_print(ANDROID_LOG_INFO, "BKA_GFX", "TRI dispatch 0x34 w0=0x%08X", c.w0); Cmd_Tri1_F3DEX2(c); break;

            case 0xB1: __android_log_print(ANDROID_LOG_INFO, "BKA_GFX", "TRI dispatch 0xB1 w0=0x%08X", c.w0); Cmd_Tri2(c); break;
            case 0x03: Cmd_MoveMem(c); break;
            case 0xBC: Cmd_MoveWord(c); break;

            case 0x06: {
                uint32_t raw_addr = c.w1;
                void *dl_ptr = RDP_TranslateAddr(raw_addr);
                __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
                    "G_DL: addr=0x%08X resolved=%p", raw_addr, dl_ptr);
                if (!dl_ptr) {
                    __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
                        "G_DL: cannot resolve addr=0x%08X", raw_addr);
                    break;
                }
                if (depth >= 63) {
                    __android_log_print(ANDROID_LOG_ERROR, "BKA_GFX",
                        "G_DL: max depth reached");
                    break;
                }

                // Save current position/end for ENDDL
                stack[depth].ptr = cur;
                stack[depth].end = cur_end;
                stack_stride[depth] = current_stride;
                depth++;

                cur = (uint8_t*)dl_ptr;
                // Use a safe upper bound based on MAX_DL_CMDS to avoid
                // running off into non-DL data if this nested list lacks ENDDL.
                cur_end = cur + (MAX_DL_CMDS * current_stride);
                dl_cmds = 0;
                zero_run = 0;
                break;
            }

            case 0xB8:
                // G_POPMTX in F3DEX/F3DEX2. The software RDP currently
                // does not maintain a full matrix stack, so treat it as
                // a safe no-op rather than crashing.
                break;

            case 0xDF:
                if (depth > 0) {
                    depth--;
                    cur = stack[depth].ptr;
                    cur_end = stack[depth].end;
                    current_stride = stack_stride[depth];
                    dl_cmds = 0;
                    zero_run = 0;
                } else {
                    __android_log_print(ANDROID_LOG_INFO, "BKA_GFX",
                        "ENDDL top-level, vertices=%d", s_rdp.dmemVertexCount);
                    return;
                }
                break;

            case 0x14:
            case 0x1C:

            case 0x40:
                Cmd_LoadTLUT(c);
                break;

            case 0xA4:
            case 0xB0:
                Cmd_LoadBlock(c);
                break;

            case 0x98:
            case 0xA1:
                Cmd_SetTImg(c);
                break;

            case 0x84:
                Cmd_SetOtherModeL(c);
                break;

            case 0x60:
                Cmd_SetOtherModeH(c);
                break;
case 0xDC:
                Cmd_MoveMem(c);
                break;
            case 0x16: // G_TEXRECTFLIP - textured rectangle flip
            case 0x1D: // G_TEXRECT - textured rectangle
                Cmd_TexRect(c);
                break;
            case 0x30: // G_LOADUCODE - load microcode (no-op for software RDP)
            case 0x39: // G_SETTILESIZE - set tile size (handled by 0xF2)
            case 0x3A: // G_LOADBLOCK - load texture block (handled by 0xF3)
            case 0x41: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0x45: // G_SETTILE - set tile (handled by 0xF5)
            case 0x50: // G_SETSCISSOR - set scissor box (can be no-op)
            case 0x57: // G_SETOTHERMODE_L - set other mode L (handled by 0xE2)
            case 0x63: // G_SETCOMBINE - set combine mode (handled by 0xFC)
            case 0x65: // G_SETOTHERMODE_H - set other mode H (handled by 0xE3)
            case 0x6B: // G_SETTILESIZE - set tile size (handled by 0xF2)
            case 0x71: // G_SETTILE - set tile (handled by 0xF5)
            case 0x72: // G_SETTILE - set tile (handled by 0xF5)
            case 0x7D: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0x80: // G_RDPHALF_1 - RDP half command
            case 0x81: // G_RDPHALF_2 - RDP half command
            case 0x8C: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0x8D: // G_LOADBLOCK - load texture block (handled by 0xF3)
            case 0x91: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0x95: // G_SETTILESIZE - set tile size (handled by 0xF2)
            case 0x99: // G_SETOTHERMODE_L - set other mode L (handled by 0xE2)
            case 0xA6: // G_LOADTLUT - load texture lookup table (handled by 0x40)
            case 0xA7: // G_SETTILE - set tile (handled by 0xF5)
            case 0xA9: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0xAD: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0xB2: // G_SETTILE - set tile (handled by 0xF5)
            case 0xB4: // G_LOADBLOCK - load texture block (handled by 0xF3)
            case 0xC6: // G_SETTILESIZE - set tile size (handled by 0xF2)
            case 0xC8: // G_SETTILE - set tile (handled by 0xF5)
            case 0xCB: // G_RDPHALF_1 - RDP half command
            case 0xCC: // G_LOADBLOCK - load texture block (handled by 0xF3)
            case 0xDE: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0xF8: // G_SETTILESIZE - set tile size (handled by 0xF2)
            case 0xF9: // G_SETTILE - set tile (handled by 0xF5)
                break;
            case 0x12: // G_LOADUCODE - load microcode (no-op)
            case 0x20: // G_RDPHALF_1 - RDP half command
            case 0x21: // G_RDPHALF_2 - RDP half command
            case 0x36: // G_SETTILESIZE - set tile size (handled by 0xF2)
            case 0x0A: // G_SETTIMG - set texture image (handled by 0xFD)
            case 0xD4: // G_LOADBLOCK - load texture block (handled by 0xF3)
            case 0xDD: // G_SETTIMG - set texture image (handled by 0xFD)
                break;
            case 0x05: // G_TEXTURE - enable texture
            case 0x11: // G_RDPHALF_1 - RDP half command
            case 0x22: // G_RDPHALF_2 - RDP half command
            case 0x2B: // G_SETTIMG - set texture image
            case 0x3C: // G_SETTILESIZE - set tile size
            case 0x48: // G_SETTIMG - set texture image
            case 0x4B: // G_LOADBLOCK - load texture block
            case 0x4C: // G_SETTILE - set tile
            case 0x54: // G_SETSCISSOR - set scissor box
            case 0x62: // G_SETTILESIZE - set tile size
            case 0x6A: // G_SETTIMG - set texture image
            case 0x6C: // G_SETTILE - set tile
            case 0x73: // G_SETTIMG - set texture image
            case 0x87: // G_LOADBLOCK - load texture block
            case 0x96: // G_SETTILESIZE - set tile size
            case 0x9A: // G_SETTIMG - set texture image
            case 0x9D: // G_SETTILE - set tile
            case 0xAB: // G_SETTIMG - set texture image
            case 0xD0: // G_LOADBLOCK - load texture block
            case 0xEB: // G_SETTIMG - set texture image
                break;
default:
                __android_log_print(ANDROID_LOG_WARN, "BKA_GFX",
                    "Stub: opcode 0x%02X not fully implemented", opcode);
                break;
        }
    }
}
