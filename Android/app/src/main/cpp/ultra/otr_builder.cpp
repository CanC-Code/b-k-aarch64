// File: ultra/otr_builder.cpp
// Purpose: Build BK OTR from ROM + embedded YAML
// Fully memory-based, deterministic, version-aware

#include "otr_builder.h"
#include "otr_generator.h"
#include <vector>
#include <cstdint>
#include <cstring>
#include <android/log.h>

#define LOG_TAG "BK_OTR"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ------------------------------------------------------------
// Build OTR in-memory
// ------------------------------------------------------------
bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    const char* yamlData,
    size_t yamlSize,
    std::vector<uint8_t>& outOTR
) {
    if (!romData || romSize == 0) {
        LOGE("Invalid ROM data");
        return false;
    }
    if (!yamlData || yamlSize == 0) {
        LOGE("Invalid YAML data");
        return false;
    }

    OTRGenerator generator;
    bool success = generator.generateOTR(
        romData,
        romSize,
        yamlData,
        yamlSize,
        outOTR
    );

    if (!success) {
        LOGE("OTRGenerator failed");
        return false;
    }

    LOGI("OTR generated: %zu bytes", outOTR.size());
    return true;
}