#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include <functional>

class OTRGenerator {
public:
    struct RomInfo {
        std::string version;
        // Add other info if needed
    };

    using ProgressCallback = std::function<void(float)>;

    OTRGenerator() = default;

    // Set the progress callback
    void setProgressCallback(ProgressCallback cb) {
        progressCallback = cb;
    }

    // Detect ROM version
    static bool detectRomVersion(const uint8_t* romData, size_t romSize, RomInfo& outInfo);

    // Load YAML file from asset manager
    static std::vector<uint8_t> loadYAMLAsset(void* mgr, const char* assetPath);

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