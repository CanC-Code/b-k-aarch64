#pragma once

#include <cstdint>
#include <vector>
#include <string>
#include <functional>

class OTRGenerator {
public:
    struct RomInfo {
        std::string version;
    };

    using ProgressCallback = std::function<void(float)>;

    OTRGenerator();

    // Progress callback
    void setProgressCallback(ProgressCallback cb);

    // ROM detection
    static bool detectRomVersion(
        const uint8_t* romData,
        size_t romSize,
        RomInfo& outInfo
    );

    // Main generation entry point
    bool generateOTR(
        const uint8_t* romData,
        size_t romSize,
        const uint8_t* yamlData,
        size_t yamlSize,
        std::vector<uint8_t>& outOTR
    );

private:
    void reportProgress(float value);

    ProgressCallback progressCallback;
};