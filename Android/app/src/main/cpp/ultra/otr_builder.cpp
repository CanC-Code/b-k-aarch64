#include "assets_manifest.h"
#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <android/log.h>

#define LOG_TAG "OTR_BUILDER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Global manifest state
std::vector<AssetEntry> g_active_manifest;
int g_rom_version = ROM_VERSION_UNKNOWN;

/**
 * Detects the ROM version based on the N64 header.
 * Offset 0x3E: Region (P = PAL, E = US)
 * Offset 0x3B: Version (0x00, 0x01, etc)
 */
int detect_rom_version(const uint8_t* rom_data, size_t size) {
    if (size < 0x40) return ROM_VERSION_UNKNOWN;

    char region = (char)rom_data[0x3E];
    uint8_t version = rom_data[0x3B];

    LOGI("Detecting ROM: Region %c, Version %d", region, version);

    if (region == 'E' || region == 'J') {
        // Typically US/JP are similar in many decomp projects
        return ROM_VERSION_US;
    } else if (region == 'P') {
        return ROM_VERSION_PAL;
    }

    return ROM_VERSION_UNKNOWN;
}

/**
 * In a real implementation, you would use a YAML parser (like mini-yaml)
 * to load the assets from the Android AssetManager.
 */
bool load_manifest_for_version(int version) {
    g_active_manifest.clear();
    std::string manifest_path;

    if (version == ROM_VERSION_US) {
        manifest_path = "decompressed.us.v10.yaml";
    } else if (version == ROM_VERSION_PAL) {
        manifest_path = "decompressed.pal.yaml";
    } else {
        LOGE("Unsupported ROM version for manifest loading");
        return false;
    }

    LOGI("Loading manifest: %s", manifest_path.c_str());
    
    // Placeholder: Logic to call AssetManager and parse YAML goes here
    // For now, we assume the manifest is loaded into g_active_manifest
    return true;
}

extern "C" void build_otr_from_rom(uint8_t* rom_data, size_t size) {
    g_rom_version = detect_rom_version(rom_data, size);
    
    if (load_manifest_for_version(g_rom_version)) {
        LOGI("Manifest loaded successfully. Starting OTR build...");
        
        // Example usage of g_active_manifest
        // for (const auto& asset : g_active_manifest) { ... }
    } else {
        LOGE("Failed to load manifest. Cannot build OTR.");
    }
}
