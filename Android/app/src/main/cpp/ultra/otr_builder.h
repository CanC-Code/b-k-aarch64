#pragma once

#include <vector>
#include <cstdint>
#include <string>
#include <android/asset_manager.h>

// Forward declaration only — no namespace conflicts
class OTRGenerator;

// High-level entry point used by JNI / wrapper
bool buildOTRForROM(
    AAssetManager* assetManager,
    const uint8_t* romData,
    size_t romSize,
    std::vector<uint8_t>& outOTR
);

// Optional legacy path (keep only if still used)
bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    const char* yamlData,
    size_t yamlSize,
    std::vector<uint8_t>& outOTR
);