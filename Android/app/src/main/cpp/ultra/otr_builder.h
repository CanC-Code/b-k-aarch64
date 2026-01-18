#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>
#include <android/asset_manager.h>

namespace OTRGenerator {
    using ProgressCallback = std::function<void(float)>;
}

// Build a BK/OTR file from raw ROM data
bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    const char* outputPath,
    const char* gameName,
    OTRGenerator::ProgressCallback progress
);

// Build OTR from ROM vector
bool buildOTRForROM(
    AAssetManager* mgr,
    const uint8_t* romData,
    size_t romSize,
    const char* outOTR,
    OTRGenerator::ProgressCallback progress
);