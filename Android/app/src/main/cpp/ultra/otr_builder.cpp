// File: app/src/main/cpp/ultra/otr_builder.cpp

#include <cstdint>
#include <vector>
#include <cstring>
#include <fstream>
#include <android/log.h>

#define LOG_TAG "BK_OTR"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

extern "C" {

// ------------------------------------------------------------
// Internal OTR storage (single owner)
// ------------------------------------------------------------
static std::vector<uint8_t> BK_OTR;

// ------------------------------------------------------------
// Core OTR builder
// ------------------------------------------------------------
void core1_loadOTR(uint8_t* romData, size_t romSize)
{
    if (!romData || romSize == 0) {
        LOGE("Invalid ROM input");
        return;
    }

    BK_OTR.clear();
    BK_OTR.reserve(romSize + 0x1000);

    // --------------------------------------------------------
    // Minimal deterministic OTR container layout
    // (header + raw ROM payload for now)
    // --------------------------------------------------------
    const char header[] = "BKOTR\0\1";

    BK_OTR.insert(
        BK_OTR.end(),
        reinterpret_cast<const uint8_t*>(header),
        reinterpret_cast<const uint8_t*>(header) + sizeof(header)
    );

    BK_OTR.insert(BK_OTR.end(), romData, romData + romSize);

    LOGI("OTR built successfully (%zu bytes)", BK_OTR.size());
}

// ------------------------------------------------------------
// OTR accessors
// ------------------------------------------------------------
uint8_t* getOTRData(size_t* outSize)
{
    if (outSize) {
        *outSize = BK_OTR.size();
    }

    return BK_OTR.empty() ? nullptr : BK_OTR.data();
}

void saveOTRToFile(const char* path)
{
    if (!path) {
        LOGE("Invalid output path");
        return;
    }

    if (BK_OTR.empty()) {
        LOGE("No OTR data to save");
        return;
    }

    std::ofstream out(path, std::ios::binary);
    if (!out) {
        LOGE("Failed to open output file");
        return;
    }

    out.write(
        reinterpret_cast<const char*>(BK_OTR.data()),
        static_cast<std::streamsize>(BK_OTR.size())
    );

    out.close();
    LOGI("OTR saved to disk (%zu bytes)", BK_OTR.size());
}

} // extern "C"