#include "otr_builder.h"
#include "otr_generator.hpp" // For OTRGenerator::ProgressCallback

#include <vector>
#include <cstring>
#include <string>
#include <iostream>

// Implementation of buildBKOTR
bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    const char* outputPath,
    const char* gameName,
    OTRGenerator::ProgressCallback progress
) {
    // Placeholder example logic
    if (!romData || romSize == 0 || !outputPath || !gameName) {
        return false;
    }

    // Simulate progress
    if (progress) progress(0.0f);

    // ...actual BK/OTR build logic goes here...

    if (progress) progress(1.0f);

    return true;
}

// Implementation of buildOTRForROM
bool buildOTRForROM(
    AAssetManager* mgr,
    const uint8_t* romData,
    size_t romSize,
    const char* outOTR,
    OTRGenerator::ProgressCallback progress
) {
    if (!romData || romSize == 0 || !outOTR) {
        return false;
    }

    // Call buildBKOTR internally
    const char* gameName = "UnknownGame"; // Placeholder
    return buildBKOTR(romData, romSize, outOTR, gameName, progress);
}