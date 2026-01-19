#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include <functional>

struct EmbeddedAsset {
    const char* name;
    const uint8_t* data;
    size_t size;
};

class OTRGenerator {
public:
    using ProgressCallback = std::function<void(float)>;

    OTRGenerator(const EmbeddedAsset* assets = nullptr, size_t count = 0)
        : embeddedAssets(assets), embeddedCount(count) {}

    // Build OTR from embedded assets
    std::vector<uint8_t> buildOTR(ProgressCallback cb = nullptr);

protected:
    void reportProgress(float p) {
        if (cb) cb(p);
    }

private:
    const EmbeddedAsset* embeddedAssets = nullptr;
    size_t embeddedCount = 0;
    ProgressCallback cb = nullptr;
};