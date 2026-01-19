// File: Android/app/src/main/cpp/ultra/otr_builder.cpp
// Purpose: Builds OTR data using assets loaded via NativeBridge

#include "otr_builder.hpp"
#include "otr_generator.hpp"
#include "NativeBridge.hpp" // Provides readAsset
#include <android/asset_manager_jni.h>
#include <vector>
#include <cstdint>

void buildOTR(AAssetManager* assetManager) {
    OTRGenerator generator;

    // Load palettes and YAML data using the global readAsset function
    auto palData = readAsset(assetManager, "otr_yaml/decompressed.pal.yaml");
    auto usData  = readAsset(assetManager, "otr_yaml/decompressed.us.v10.yaml");

    // Pass loaded data to the generator
    generator.generateOTR(palData, usData);
}