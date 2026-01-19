#pragma once
#include <vector>
#include <cstdint>
#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>

class OTRGenerator {
public:
    explicit OTRGenerator(AAssetManager* mgr) : assetManager(mgr) {}
    ~OTRGenerator() = default;

    bool generateOTR(const std::vector<uint8_t>& romData);

    const std::vector<uint8_t>& getOTRBuffer() const { return otrBuffer; }
    void clear() { otrBuffer.clear(); }

private:
    AAssetManager* assetManager;
    std::vector<uint8_t> otrBuffer;

    std::vector<uint8_t> loadYAMLAsset(const char* assetName);
};