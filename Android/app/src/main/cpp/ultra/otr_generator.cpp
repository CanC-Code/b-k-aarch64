#include "otr_generator.hpp"
#include <android/log.h>
#include <stdexcept>

#define LOG_TAG "OTR_GEN"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

std::vector<uint8_t> OTRGenerator::buildOTR(ProgressCallback callback) {
    cb = callback;
    std::vector<uint8_t> out;

    if (!embeddedAssets || embeddedCount == 0) {
        LOGE("No embedded assets provided");
        return out;
    }

    try {
        size_t totalSteps = embeddedCount;
        for (size_t i = 0; i < embeddedCount; ++i) {
            const EmbeddedAsset& asset = embeddedAssets[i];
            out.insert(out.end(), asset.data, asset.data + asset.size);

            // Report progress
            reportProgress(static_cast<float>(i + 1) / static_cast<float>(totalSteps));
        }

        reportProgress(1.0f);
        LOGI("OTR build completed: %zu bytes", out.size());

    } catch (const std::exception& e) {
        LOGE("Exception during OTR build: %s", e.what());
    } catch (...) {
        LOGE("Unknown exception during OTR build");
    }

    return out;
}