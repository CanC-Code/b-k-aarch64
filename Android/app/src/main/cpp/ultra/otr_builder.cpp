// File: Android/app/src/main/cpp/ultra/otr_builder_bin.cpp
#include <cstdint>
#include <vector>
#include <android/log.h>
#include <atomic>
#include <cstring>
#include <cstdio>

#define LOG_TAG "BKA_OTR_BIN"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// ---- Global OTR ----
static std::vector<uint8_t> BK_OTR;
static std::atomic<float> g_progress{0.0f};

// ---- Segment descriptor from BIN ----
struct OTRSegment {
    uint32_t offset;
    uint32_t size;
};

// ---- Load OTR from precomputed BIN ----
extern "C"
bool loadOTRFromBin(const char* binPath) {
    BK_OTR.clear();
    g_progress = 0.0f;
    if (!binPath) return false;

    FILE* f = fopen(binPath, "rb");
    if (!f) {
        LOGI("Failed to open BIN: %s", binPath);
        return false;
    }

    // Read entry count (first 4 bytes)
    uint32_t entryCount = 0;
    if (fread(&entryCount, 4, 1, f) != 1) {
        fclose(f);
        LOGI("Failed to read entry count from BIN");
        return false;
    }

    if (entryCount == 0) {
        fclose(f);
        LOGI("BIN has no entries");
        return false;
    }

    struct EntryHeader { uint32_t offset; uint32_t size; };
    std::vector<EntryHeader> entries(entryCount);

    if (fread(entries.data(), sizeof(EntryHeader), entryCount, f) != entryCount) {
        fclose(f);
        LOGI("Failed to read entry headers");
        return false;
    }

    // Copy each entry into BK_OTR
    for (uint32_t i = 0; i < entryCount; i++) {
        const auto& e = entries[i];
        if (e.size == 0) continue;

        // Seek to offset
        if (fseek(f, e.offset, SEEK_SET) != 0) {
            fclose(f);
            LOGI("Failed to seek to offset 0x%X", e.offset);
            return false;
        }

        size_t curSize = BK_OTR.size();
        BK_OTR.resize(curSize + e.size);
        if (fread(BK_OTR.data() + curSize, 1, e.size, f) != e.size) {
            fclose(f);
            LOGI("Failed to read segment %u", i);
            return false;
        }

        g_progress = float(i + 1) / entryCount;
        LOGI("Segment %u: offset 0x%X size %u", i, e.offset, e.size);
    }

    fclose(f);

    // Pad to 16 bytes
    size_t pad = (16 - (BK_OTR.size() % 16)) % 16;
    BK_OTR.insert(BK_OTR.end(), pad, 0);

    g_progress = 1.0f;
    LOGI("Loaded BIN OTR: %zu bytes (+%zu padding)", BK_OTR.size(), pad);
    return true;
}

// ---- Accessors ----
extern "C" uint8_t* getOTRData(size_t* outSize) {
    if (outSize) *outSize = BK_OTR.size();
    return BK_OTR.empty() ? nullptr : BK_OTR.data();
}

extern "C" float getOTRProgress() { return g_progress.load(); }

extern "C"
bool saveOTRToFile(const char* path) {
    if (!path || BK_OTR.empty()) return false;
    FILE* f = fopen(path, "wb");
    if (!f) return false;
    fwrite(BK_OTR.data(), 1, BK_OTR.size(), f);
    fclose(f);
    LOGI("Saved BK.OTR to %s (%zu bytes)", path, BK_OTR.size());
    return true;
}