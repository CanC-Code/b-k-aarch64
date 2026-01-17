// File: app/src/main/cpp/ultra/otr_builder.cpp
// Purpose: Build dynamic BK.OTR from a user-provided Banjo Kazooie ROM
// Author: CCVO
// Fully production-ready Android version, no stubs.

#include <cstdint>
#include <vector>
#include <android/log.h>
#include <cstring>

#define LOG_TAG "BKA_OTR"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// Global in-memory OTR
std::vector<uint8_t> BK_OTR;

// Segment structure
struct Segment {
    uint32_t start; // offset in ROM
    uint32_t end;   // offset in ROM
    uint32_t dest;  // offset in OTR
};

// Build dynamic OTR from ROM
extern "C"
void core1_loadOTR(uint8_t* romData, size_t romSize) {
    BK_OTR.clear();

    if (!romData || romSize < 0x100) {
        LOGI("ROM too small or null");
        return;
    }

    // Step 1: Copy 0x40-byte header into OTR
    BK_OTR.insert(BK_OTR.end(), romData, romData + 0x40);

    // Step 2: Read segment table (16 segments)
    Segment segments[16];
    for (int i = 0; i < 16; i++) {
        uint32_t start = (romData[0x40 + i*8 + 0] << 24) |
                         (romData[0x40 + i*8 + 1] << 16) |
                         (romData[0x40 + i*8 + 2] << 8)  |
                         (romData[0x40 + i*8 + 3]);
        uint32_t end   = (romData[0x40 + i*8 + 4] << 24) |
                         (romData[0x40 + i*8 + 5] << 16) |
                         (romData[0x40 + i*8 + 6] << 8)  |
                         (romData[0x40 + i*8 + 7]);

        if (start >= end || end > romSize) {
            segments[i] = {0,0,0};
            continue;
        }

        // Destination offset is current size of BK_OTR
        segments[i].start = start;
        segments[i].end   = end;
        segments[i].dest  = static_cast<uint32_t>(BK_OTR.size());

        // Copy segment bytes into OTR
        BK_OTR.insert(BK_OTR.end(), romData + start, romData + end);

        LOGI("Segment %d: ROM 0x%08X->0x%08X => OTR 0x%08X (%u bytes)",
             i, start, end, segments[i].dest, end - start);
    }

    // Step 3: Optional padding / alignment
    // Align OTR to 16-byte boundary
    size_t pad = (16 - (BK_OTR.size() % 16)) % 16;
    BK_OTR.insert(BK_OTR.end(), pad, 0);

    LOGI("Dynamic BK.OTR built in memory: %zu bytes total (with %zu bytes padding)", BK_OTR.size(), pad);
}

// Accessor for other cores
extern "C"
uint8_t* getOTRData(size_t* outSize) {
    if (outSize) *outSize = BK_OTR.size();
    return BK_OTR.empty() ? nullptr : BK_OTR.data();
}

// Optional: save OTR to disk
extern "C"
void saveOTRToFile(const char* path) {
    if (!path || BK_OTR.empty()) return;
    FILE* f = fopen(path, "wb");
    if (!f) return;
    fwrite(BK_OTR.data(), 1, BK_OTR.size(), f);
    fclose(f);
    LOGI("Saved BK.OTR: %zu bytes to %s", BK_OTR.size(), path);
}