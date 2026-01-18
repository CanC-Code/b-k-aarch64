#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include <functional>
#include <android/asset_manager.h>

class OTRGenerator {
public:
    struct RomInfo {
        std::string version;
        // Future: add more metadata fields if needed
    };

    using ProgressCallback = std::function<void(float)>;

    OTRGenerator() = default;

    // Assign a progress callback for real-time updates
    void setProgressCallback(ProgressCallback cb) {
        progressCallback = cb;
    }

    // Detect ROM version (returns true if recognized)
    static bool detectRomVersion(const uint8_t* romData, size_t romSize, RomInfo& outInfo);

    // Load YAML file from Android assets
    static std::vector<uint8_t> loadYAMLAsset(AAssetManager* mgr, const char* assetPath);

    // Generate OTR from ROM + YAML
    bool generateOTR(const uint8_t* romData,
                     size_t romSize,
                     const char* yamlData,
                     size_t yamlSize,
                     std::vector<uint8_t>& outOTR);

protected:
    void reportProgress(float p) {
        if (progressCallback) progressCallback(p);
    }

private:
    ProgressCallback progressCallback;
};