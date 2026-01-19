#pragma once

#include <vector>
#include <string>
#include <cstdint>
#include <android/log.h>

#ifndef LOG_TAG
#define LOG_TAG "OTR_ASSETS"
#endif
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Structure representing an embedded asset
struct OTRAsset {
    std::string name;
    std::vector<uint8_t> data;
};

// Stub: loads your embedded ROM/YAML data
inline std::vector<OTRAsset> loadEmbeddedOTRAssets() {
    std::vector<OTRAsset> assets;

    // Add the embedded ROM and YAMLs here
    // For example placeholders:
    extern const uint8_t embedded_pal_yaml[];
    extern const size_t embedded_pal_yaml_size;
    extern const uint8_t embedded_us_yaml[];
    extern const size_t embedded_us_yaml_size;
    extern const uint8_t embedded_rom[];
    extern const size_t embedded_rom_size;

    assets.push_back({"decompressed.pal.yaml", std::vector<uint8_t>(embedded_pal_yaml, embedded_pal_yaml + embedded_pal_yaml_size)});
    assets.push_back({"decompressed.us.v10.yaml", std::vector<uint8_t>(embedded_us_yaml, embedded_us_yaml + embedded_us_yaml_size)});
    assets.push_back({"rom.z64", std::vector<uint8_t>(embedded_rom, embedded_rom + embedded_rom_size)});

    return assets;
}