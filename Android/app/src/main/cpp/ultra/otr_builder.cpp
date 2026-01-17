// File: Android/app/src/main/cpp/ultra/otr_builder.cpp
// Purpose: Build dynamic BK.OTR from a user-provided Banjo-Kazooie ROM
// Author: CCVO
// Fully production-ready Android version, with OTR progress

#include <cstdint>
#include <vector>
#include <android/log.h>
#include <cstring>
#include <cstdio>

#define LOG_TAG "BKA_OTR"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ---- Global in-memory OTR ----
static std::vector<uint8_t> BK_OTR;

// ---- OTR progress (0.0 - 1.0) ----
static float BK_OTR_progress = 0.0f;

// ---- Segment structure ----
struct Segment {
    uint32_t start; // offset in ROM
    uint32_t end;   // offset in ROM
    uint32_t dest;  // offset in OTR
};

// ---- Build dynamic OTR from ROM ----
extern "C"
void core1_loadOTR(uint8_t* romData, size_t romSize) {
    BK_OTR.clear();
    BK_OTR_progress = 0.0f;

    if (!romData || romSize < 0x100) {
        LOGI("ROM too small or null");
        return;
    }

    // Step 1: Copy 0x40-byte header
    BK_OTR.insert(BK_OTR.end(), romData, romData + 0x40);

    // Step 2: Calculate total bytes for progress
    uint32_t totalBytes = 0;
    for (int i=0; i<16; i++) {
        uint32_t start = (romData[0x40 + i*8 + 0] << 24) |
                         (romData[0x40 + i*8 + 1] << 16) |
                         (romData[0x40 + i*8 + 2] << 8)  |
                         (romData[0x40 + i*8 + 3]);
        uint32_t end   = (romData[0x40 + i*8 + 4] << 24) |
                         (romData[0x40 + i*8 + 5] << 16) |
                         (romData[0x40 + i*8 + 6] << 8)  |
                         (romData[0x40 + i*8 + 7]);
        if (start < end && end <= romSize) totalBytes += end-start;
    }

    Segment segments[16];
    uint32_t copiedBytes = 0;

    // Step 3: Copy each segment into OTR
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

        segments[i].start = start;
        segments[i].end   = end;
        segments[i].dest  = static_cast<uint32_t>(BK_OTR.size());

        BK_OTR.insert(BK_OTR.end(), romData + start, romData + end);

        copiedBytes += (end - start);
        BK_OTR_progress = totalBytes ? static_cast<float>(copiedBytes) / totalBytes : 0.0f;

        LOGI("Segment %d: ROM 0x%08X->0x%08X => OTR 0x%08X (%u bytes) Progress: %.2f%%",
             i, start, end, segments[i].dest, end - start, BK_OTR_progress*100.0f);
    }

    // Step 4: Pad to 16-byte alignment
    size_t pad = (16 - (BK_OTR.size() % 16)) % 16;
    BK_OTR.insert(BK_OTR.end(), pad, 0);

    BK_OTR_progress = 1.0f;
    LOGI("Dynamic BK.OTR built: %zu bytes (+%zu padding)", BK_OTR.size(), pad);
}

// ---- Accessors ----
extern "C"
uint8_t* getOTRData(size_t* outSize) {
    if (outSize) *outSize = BK_OTR.size();
    return BK_OTR.empty() ? nullptr : BK_OTR.data();
}

extern "C"
void saveOTRToFile(const char* path) {
    if (!path || BK_OTR.empty()) return;
    FILE* f = fopen(path, "wb");
    if (!f) return;
    fwrite(BK_OTR.data(), 1, BK_OTR.size(), f);
    fclose(f);
    LOGI("Saved BK.OTR: %zu bytes to %s", BK_OTR.size(), path);
}

// ---- OTR progress accessor for Java ----
extern "C"
float getOTRProgress() {
    return BK_OTR_progress;
}

// ---- JNI bridge for progress ----
#include <jni.h>
extern "C"
JNIEXPORT jfloat JNICALL
Java_com_bkawrapper_NativeBridge_getOTRProgress(JNIEnv*, jclass) {
    return BK_OTR_progress;
}