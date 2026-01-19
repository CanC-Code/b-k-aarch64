// otr_generator.hpp
#pragma once
#include <vector>
#include <android/asset_manager.h>

class OTRGenerator {
    AAssetManager* assetManager;
    std::vector<uint8_t> generatedData;
    float progress;

public:
    explicit OTRGenerator(AAssetManager* mgr) : assetManager(mgr), progress(0.0f) {}

    bool generate(const std::vector<uint8_t>& romData, const char* yamlPath);
    float getProgress() const { return progress; }
    void loadIntoRenderer(); // push generatedData to GLRenderer
};