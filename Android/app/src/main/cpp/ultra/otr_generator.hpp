#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include <functional>
#include <android/asset_manager.h>
#include <android/log.h>

#define LOG_TAG "OTR_GEN"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// -----------------------------
// OTR Generator
// -----------------------------
class OTRGenerator {
public:
    struct RomInfo {
        std::string version;
        // Future: add metadata fields here
    };

    using ProgressCallback = std::function<void(float)>;

    OTRGenerator() = default;

    // Assign progress callback
    void setProgressCallback(ProgressCallback cb) { progressCallback = cb; }

    // Detect ROM version
    static bool detectRomVersion(const uint8_t* romData, size_t romSize, RomInfo& outInfo);

    // Generate OTR from ROM + dynamically loaded YAMLs
    bool generate(
        const uint8_t* romData,
        size_t romSize,
        const std::vector<std::pair<std::string, std::vector<uint8_t>>>& yamlAssets
    );

    // Retrieve generated OTR
    const std::vector<uint8_t>& getData() const { return outOTR; }

protected:
    void reportProgress(float p) { if (progressCallback) progressCallback(p); }

private:
    ProgressCallback progressCallback;
    std::vector<uint8_t> outOTR;
};