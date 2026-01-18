// File: otr_builder.cpp
// Purpose: Deterministic ROM → OTR loader (NDK/Android-safe, embedded YAML)

#include <cstdint>
#include <cstddef>
#include <vector>
#include <string>
#include <unordered_map>
#include <android/log.h>

#include "otr_generator.h"

#define LOG_TAG "OTR_BUILDER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ---------------------------------------------------------------------
// Embedded YAML layouts (example, replace with actual content)
// ---------------------------------------------------------------------
extern const char embedded_us_v10_yaml[];
extern const char embedded_pal_yaml[];
// Add additional embedded YAMLs as needed

// Map known ROM SHA1 -> embedded YAML pointer
static const std::unordered_map<std::string, const char*> g_romToYaml = {
    { "1fb13cad402518d3ae9a8dc4b52c5c54b2a4adc7", embedded_us_v10_yaml },
    { "<PAL_SHA1_HERE>", embedded_pal_yaml }
};

// ---------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------
bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    std::vector<uint8_t>& outOTR
) {
    outOTR.clear();

    if (!romData || romSize == 0) {
        LOGE("Invalid ROM input");
        return false;
    }

    // --- SHA1 detect ROM ---
    OTRGenerator generator;
    std::string sha1 = generator.sha1Hex(romData, romSize);
    LOGI("ROM SHA1: %s", sha1.c_str());

    auto it = g_romToYaml.find(sha1);
    if (it == g_romToYaml.end()) {
        LOGE("Unsupported ROM");
        return false;
    }

    const char* yamlData = it->second;
    size_t yamlSize = strlen(yamlData);

    // --- Generate OTR directly from embedded YAML ---
    if (!generator.generateOTR(romData, romSize, yamlData, yamlSize, outOTR)) {
        LOGE("Failed to generate OTR from YAML");
        return false;
    }

    LOGI("OTR generated in-memory: %zu bytes", outOTR.size());
    return true;
}