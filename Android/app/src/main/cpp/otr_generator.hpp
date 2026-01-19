#pragma once

#include <cstddef>
#include <cstdint>
#include <android/asset_manager.h>
#include <functional>

bool GenerateOTR(
    const uint8_t* romData,
    size_t romSize,
    AAssetManager* assetManager,
    const char* yamlAssetPath,
    const char* outputDir,
    std::function<void(float)> progressCallback
);