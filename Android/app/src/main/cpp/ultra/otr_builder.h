#pragma once
#include <vector>
#include <cstdint>
#include <string>
#include <functional>
#include <android/asset_manager_jni.h>
#include "otr_generator.h"

// Callback type for progress updates (0.0 → 1.0)
using ProgressCallback = std::function<void(float)>;

// Build OTR using embedded YAML per ROM version
bool buildOTRForROM(
    AAssetManager* mgr,
    const uint8_t* romData,
    size_t romSize,
    std::vector<uint8_t>& outOTR,
    ProgressCallback progress = nullptr
);

// Legacy: Build OTR using preloaded YAML in memory
bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    const char* yamlData,
    size_t yamlSize,
    std::vector<uint8_t>& outOTR,
    ProgressCallback progress = nullptr
);