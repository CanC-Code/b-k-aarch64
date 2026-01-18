#include "ultra/otr_builder.h"

#include <vector>
#include <cstdint>
#include <iostream>
#include <android/asset_manager.h>

// Example wrapper function to build OTR from a ROM vector
bool buildOTRWrapper(const std::vector<uint8_t>& romVec, const char* outOTR) {
    if (romVec.empty() || !outOTR) {
        std::cerr << "Invalid ROM data or output path." << std::endl;
        return false;
    }

    // Call buildOTRForROM from otr_builder
    // Passing nullptr for AAssetManager since this is a simple wrapper example
    bool success = buildOTRForROM(nullptr, romVec.data(), romVec.size(), outOTR,
                                  [](float progress) {
                                      std::cout << "Progress: " << (progress * 100.0f) << "%" << std::endl;
                                  });

    if (!success) {
        std::cerr << "Failed to build OTR." << std::endl;
    }

    return success;
}

// Example main wrapper entry (optional, can be called from JNI)
extern "C" bool buildOTRFromROM(const uint8_t* romData, size_t romSize, const char* outOTR) {
    if (!romData || romSize == 0 || !outOTR) {
        return false;
    }

    std::vector<uint8_t> romVec(romData, romData + romSize);
    return buildOTRWrapper(romVec, outOTR);
}