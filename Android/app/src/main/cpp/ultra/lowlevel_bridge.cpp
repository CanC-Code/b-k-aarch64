#include "n64_os_types_cpp.h"
// File: Android/app/src/main/cpp/ultra/lowlevel_bridge.cpp

#include <sys/mman.h>
#include <errno.h>
#include <android/log.h>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <stdint.h>
#include <GLES2/gl2.h>

#define LOG_TAG "BKA_MEM"

#define BKA_RDRAM_ALLOC_SIZE  0x1001000
#define N64_REG_SPACE_SIZE    0x1000000
#define N64_PIF_SPACE_SIZE    0x0010000
#define N64_ROM_SPACE_SIZE    0x04000000

#define MI_INTR_REG_IDX       (0x00300008 / 4)
#define MI_INTR_VI            0x08

#define N64_HEAP_OFFSET       0x002D500
#define N64_HEAP_SIZE         0x211120

uint8_t* gN64_RDRAM    = nullptr;
uint32_t* gN64_Reg_Base = nullptr;
uint32_t* gN64_PIF_Base = nullptr;
uint8_t* gN64_ROM_Base = nullptr;

// -----------------------------------------------------------------------
// Framebuffer allocation (moved from missing_stubs.c for C++ linkage)
// The game draws into a double-buffered framebuffer in N64 RDRAM.
// Each buffer is 292×216×2 bytes, placed at offset 0x400000 (4 MB).
// The video plugin reads from gN64_RDRAM + g_active_fb_offset.
// -----------------------------------------------------------------------
#define FB_WIDTH   292
#define FB_HEIGHT  216
#define FB_SIZE    (FB_WIDTH * FB_HEIGHT * sizeof(u16))

uint16_t gFramebuffers[2][FB_WIDTH * FB_HEIGHT];
uint32_t g_active_fb_offset = 0x400000;

extern "C" {

    void HLE_TriggerN64Event(int event_id);

    // gFramebufferWidth/Height are defined in the recompiled game code
    // (src/core1/vimgr.c or similar). They default to 292x216.
    extern s32 gFramebufferWidth;
    extern s32 gFramebufferHeight;

    void InitN64Registers(const char* assetDir) {
        if (gN64_RDRAM != nullptr && gN64_Reg_Base != nullptr &&
            gN64_PIF_Base != nullptr && gN64_ROM_Base != nullptr) {
            return;
        }

        gN64_RDRAM = (uint8_t*)mmap(nullptr, BKA_RDRAM_ALLOC_SIZE,
                                    PROT_READ | PROT_WRITE,
                                    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        gN64_Reg_Base = (uint32_t*)mmap(nullptr, N64_REG_SPACE_SIZE,
                                        PROT_READ | PROT_WRITE,
                                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        gN64_PIF_Base = (uint32_t*)mmap(nullptr, N64_PIF_SPACE_SIZE,
                                        PROT_READ | PROT_WRITE,
                                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        gN64_ROM_Base = (uint8_t*)mmap(nullptr, N64_ROM_SPACE_SIZE,
                                       PROT_READ | PROT_WRITE,
                                       MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);

        if (gN64_RDRAM == MAP_FAILED || gN64_Reg_Base == MAP_FAILED ||
            gN64_PIF_Base == MAP_FAILED || gN64_ROM_Base == MAP_FAILED) {
            __android_log_print(ANDROID_LOG_FATAL, LOG_TAG,
                "Critical virtual memory mapping failure: %s", strerror(errno));
            if (gN64_RDRAM    != MAP_FAILED && gN64_RDRAM    != nullptr) munmap(gN64_RDRAM,    BKA_RDRAM_ALLOC_SIZE);
            if (gN64_Reg_Base != MAP_FAILED && gN64_Reg_Base != nullptr) munmap(gN64_Reg_Base, N64_REG_SPACE_SIZE);
            if (gN64_PIF_Base != MAP_FAILED && gN64_PIF_Base != nullptr) munmap(gN64_PIF_Base, N64_PIF_SPACE_SIZE);
            if (gN64_ROM_Base != MAP_FAILED && gN64_ROM_Base != nullptr) munmap(gN64_ROM_Base, N64_ROM_SPACE_SIZE);
            gN64_RDRAM    = nullptr;
            gN64_Reg_Base = nullptr;
            gN64_PIF_Base = nullptr;
            gN64_ROM_Base = nullptr;
            abort();
        }

        memset(gN64_RDRAM,    0, BKA_RDRAM_ALLOC_SIZE);
        memset(gN64_Reg_Base, 0, N64_REG_SPACE_SIZE);
        memset(gN64_PIF_Base, 0, N64_PIF_SPACE_SIZE);
        memset(gN64_ROM_Base, 0, N64_ROM_SPACE_SIZE);

        if (N64_HEAP_OFFSET + N64_HEAP_SIZE <= BKA_RDRAM_ALLOC_SIZE) {
            __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
                "Heap region validated: RDRAM+0x%X (0x%X bytes) for D_8002D500",
                N64_HEAP_OFFSET, N64_HEAP_SIZE);
        } else {
            __android_log_print(ANDROID_LOG_ERROR, LOG_TAG,
                "FATAL: Heap region exceeds RDRAM allocation!");
        }
        __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
            "RDRAM allocated: %zu bytes (16MB usable + 4KB overflow guard)",
            (size_t)BKA_RDRAM_ALLOC_SIZE);

        char romPath[512];
        snprintf(romPath, sizeof(romPath), "%s/rom_base.bin", assetDir);
        FILE* f = fopen(romPath, "rb");
        if (f) {
            size_t bytesRead = fread(gN64_ROM_Base, 1, N64_ROM_SPACE_SIZE, f);
            fclose(f);
            __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
                "Memory Engine Stabilized: physical ROM mapped from %s (%zu bytes).", romPath, bytesRead);
        } else {
            __android_log_print(ANDROID_LOG_WARN, LOG_TAG, "WARNING: rom_base.bin missing, fallback memory will be zeroed.");
            gN64_ROM_Base[0x3B] = 'N'; gN64_ROM_Base[0x3C] = 'B';
            gN64_ROM_Base[0x3D] = 'K'; gN64_ROM_Base[0x3E] = 'E';
        }
    }

    void HardwareRegs_Shutdown() {
        if (gN64_RDRAM)    { munmap(gN64_RDRAM,    BKA_RDRAM_ALLOC_SIZE); gN64_RDRAM    = nullptr; }
        if (gN64_Reg_Base) { munmap(gN64_Reg_Base, N64_REG_SPACE_SIZE);   gN64_Reg_Base = nullptr; }
        if (gN64_PIF_Base) { munmap(gN64_PIF_Base, N64_PIF_SPACE_SIZE);   gN64_PIF_Base = nullptr; }
        if (gN64_ROM_Base) { munmap(gN64_ROM_Base, N64_ROM_SPACE_SIZE);   gN64_ROM_Base = nullptr; }
        __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Memory Engine Closed down cleanly.");
    }

    struct BKA_ControllerPad {
        uint16_t button;
        int8_t   stick_x;
        int8_t   stick_y;
        uint8_t  errno_val;
    };
    BKA_ControllerPad gN64_ControllerData[4] = {{0, 0, 0, 0}};

    void N64_TriggerVirtualVBlankInterrupt(void) {
        if (!gN64_Reg_Base) return;
        gN64_Reg_Base[MI_INTR_REG_IDX] |= MI_INTR_VI;
        HLE_TriggerN64Event(14);
    }

    void VideoPlugin_OutputFrameTexture(uint32_t hostTextureId) {
        static int diagCount = 0;
        if (++diagCount <= 5) {
            __android_log_print(ANDROID_LOG_INFO, LOG_TAG,
                "VideoPlugin: call=%d texId=%u rdr=%p fb_ofs=%08X w=%d h=%d",
                diagCount, hostTextureId, gN64_RDRAM,
                g_active_fb_offset, gFramebufferWidth, gFramebufferHeight);
        }

        if (!gN64_RDRAM || hostTextureId == 0) return;

        uint32_t fbPhysAddr = g_active_fb_offset;
        if (fbPhysAddr == 0) return;

        uint8_t* fbBase = gN64_RDRAM + fbPhysAddr;
        if (fbBase < gN64_RDRAM || fbBase >= gN64_RDRAM + BKA_RDRAM_ALLOC_SIZE) return;

        s32 fbWidth  = gFramebufferWidth;
        s32 fbHeight = gFramebufferHeight;
        if (fbWidth <= 0 || fbWidth > 640)  fbWidth  = 320;
        if (fbHeight <= 0 || fbHeight > 480) fbHeight = 240;

        size_t fbSize = (size_t)fbWidth * fbHeight * 2;
        if (fbBase + fbSize > gN64_RDRAM + BKA_RDRAM_ALLOC_SIZE) return;

        glBindTexture(GL_TEXTURE_2D, hostTextureId);

        // Allocate conversion buffer as uint8_t to avoid any word-packing
        // endianness issues. GL_RGBA with GL_UNSIGNED_BYTE expects bytes
        // in R,G,B,A order in memory.
        static uint8_t* s_convBuffer = nullptr;
        static size_t   s_convBufferSize = 0;
        size_t neededSize = (size_t)fbWidth * fbHeight * 4;
        if (!s_convBuffer || s_convBufferSize < neededSize) {
            free(s_convBuffer);
            s_convBuffer = (uint8_t*)malloc(neededSize);
            s_convBufferSize = neededSize;
        }

        if (s_convBuffer) {
            uint16_t* src = (uint16_t*)fbBase;
            uint8_t*  dst = s_convBuffer;
            for (s32 y = 0; y < fbHeight; y++) {
                for (s32 x = 0; x < fbWidth; x++) {
                    // Read pixel directly — no byte swap.
                    // The red fill test writes uint16_t values in ARM native
                    // (little-endian) order. Real N64 game rendering will
                    // produce big-endian bytes in RDRAM, which we'll need to
                    // handle with __builtin_bswap16 when that phase arrives.
                    // For now, interpret the raw uint16_t as little-endian
                    // RGB565 with this bit layout in memory:
                    //   Byte 0 (low):  [G2 G1 G0 B4 B3 B2 B1 B0]
                    //   Byte 1 (high): [R4 R3 R2 R1 R0 G4 G3 G2]
                    // Which in uint16_t form is:
                    //   bits 15-11 = Green (high 3 bits)
                    //   bits 10-5  = Red (all 5 bits mixed with G low bits)
                    // This is scrambled. Use the raw bytes directly.
                    uint8_t  lo = ((uint8_t*)src)[0];
                    uint8_t  hi = ((uint8_t*)src)[1];
                    src++;

                    // Byte 1 (high byte in little-endian uint16_t):
                    //   bits 7-3 = Red[4:0]
                    //   bits 2-0 = Green[4:2]
                    // Byte 0 (low byte):
                    //   bits 7-5 = Green[1:0]
                    //   bits 4-0 = Blue[4:0]
                    uint8_t r = (hi & 0xF8);                    // hi bits 7-3
                    uint8_t g = ((hi & 0x07) << 5) | (lo & 0xE0) >> 3;  // hi bits 2-0 + lo bits 7-5
                    uint8_t b = (lo & 0x1F) << 3;               // lo bits 4-0
                    uint8_t a = 0xFF;

                    // Write bytes in explicit R,G,B,A order
                    *dst++ = r;
                    *dst++ = g;
                    *dst++ = b;
                    *dst++ = a;
                }
            }
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, fbWidth, fbHeight, 0,
                         GL_RGBA, GL_UNSIGNED_BYTE, s_convBuffer);
        }
    }

} // extern "C"
extern "C" int getActiveFramebuffer(void) {
    return (g_active_fb_offset == 0x400000) ? 0 : 1;
}
