// OTRGenerator.hpp
#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include <functional>
#include <android/asset_manager.h>

class OTRGenerator {
public:
    using ProgressCallback = std::function<void(float)>;

    OTRGenerator(AAssetManager* mgr) : assetManager(mgr) {}

    // Set progress callback
    void setProgressCallback(ProgressCallback cb) { progressCallback = cb; }

    // Generate OTR from ROM bytes + YAML path in assets
    bool generateOTR(const uint8_t* romData, size_t romSize,
                     const char* yamlAssetPath);

    // Access generated OTR
    const std::vector<uint8_t>& getOTR() const { return outOTR; }

private:
    void reportProgress(float p) { if(progressCallback) progressCallback(p); }
    std::vector<uint8_t> loadYAMLAsset(const char* assetPath);

    AAssetManager* assetManager = nullptr;
    std::vector<uint8_t> outOTR;
    ProgressCallback progressCallback;
};