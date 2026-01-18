#pragma once

#include <vector>
#include <cstdint>
#include <string>
#include <android/asset_manager_jni.h>

namespace OTRBuilder {

struct RomInfo {
    std::string version;
};

// Detect ROM version by SHA1
bool detectRomVersion(const uint8_t* romData, size_t romSize, RomInfo& outInfo);

// Load YAML asset from APK
std::vector<uint8_t> loadYAMLAsset(AAssetManager* mgr, const char* path);

// Generate OTR from ROM + YAML (main API)
bool buildOTRForROM(AAssetManager* mgr,
                    const uint8_t* romData,
                    size_t romSize,
                    std::vector<uint8_t>& outOTR);

// Legacy SHA1 → BIN loader
bool buildBKOTR(const uint8_t* romData,
                size_t romSize,
                const char* yamlData,
                size_t yamlSize,
                std::vector<uint8_t>& outOTR);

} // namespace OTRBuilder