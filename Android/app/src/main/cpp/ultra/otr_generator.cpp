#include "otr_generator.hpp"
#include <android/log.h>
#include <cstring>
#include <stdexcept>

#define LOG_TAG "OTR_GEN"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// -----------------------------
// Detect ROM version
// -----------------------------
bool OTRGenerator::detectRomVersion(const uint8_t* romData, size_t romSize, RomInfo& outInfo) {
    if (!romData || romSize < 4) return false;

    // Simple placeholder detection
    if (romData[0] == 'U') {
        outInfo.version = "USv1.0";
        LOGI("Detected ROM version: USv1.0");
    } else if (romData[0] == 'P') {
        outInfo.version = "PAL";
        LOGI("Detected ROM version: PAL");
    } else {
        LOGE("Unknown ROM version");
        return false;
    }

    return true;
}

// -----------------------------
// Load YAML asset from Android assets
// -----------------------------
std::vector<uint8_t> OTRGenerator::loadYAMLAsset(AAssetManager* assetManager, const char* assetPath) {
    std::vector<uint8_t> buffer;

    if (!assetManager || !assetPath) {
        LOGE("Invalid asset manager or path");
        return buffer;
    }

    AAsset* asset = AAssetManager_open(assetManager, assetPath, AASSET_MODE_STREAMING);
    if (!asset) {
        LOGE("Failed to open asset: %s", assetPath);
        return buffer;
    }

    off_t size = AAsset_getLength(asset);
    if (size <= 0) {
        LOGE("Empty asset: %s", assetPath);
        AAsset_close(asset);
        return buffer;
    }

    buffer.resize(size);
    int read = AAsset_read(asset, buffer.data(), size);
    if (read != size) {
        LOGE("Failed to read full asset: %s (read %d of %ld)", assetPath, read, size);
        buffer.clear();
    }

    AAsset_close(asset);
    return buffer;
}

// -----------------------------
// Generate OTR from ROM + YAML
// -----------------------------
bool OTRGenerator::generateOTR(
        const uint8_t* romData,
        size_t romSize,
        const char* yamlData,
        size_t yamlSize,
        std::vector<uint8_t>& outOTR
) {
    if (!romData || !yamlData || romSize == 0 || yamlSize == 0) {
        LOGE("Invalid ROM or YAML data");
        return false;
    }

    try {
        outOTR.clear();
        outOTR.reserve(romSize + yamlSize);

        const size_t totalSteps = 100;
        size_t chunkROM = romSize / totalSteps;
        size_t chunkYAML = yamlSize / totalSteps;

        // Interleaved processing simulation with progress
        for (size_t step = 0; step < totalSteps; ++step) {
            // Add chunk of ROM
            size_t romStart = step * chunkROM;
            size_t romEnd = (step == totalSteps - 1) ? romSize : romStart + chunkROM;
            outOTR.insert(outOTR.end(), romData + romStart, romData + romEnd);

            // Add chunk of YAML
            size_t yamlStart = step * chunkYAML;
            size_t yamlEnd = (step == totalSteps - 1) ? yamlSize : yamlStart + chunkYAML;
            outOTR.insert(outOTR.end(), yamlData + yamlStart, yamlData + yamlEnd);

            reportProgress(static_cast<float>(step + 1) / static_cast<float>(totalSteps));
        }

        reportProgress(1.0f);
        LOGI("OTR generation completed successfully: %zu bytes", outOTR.size());
        return true;

    } catch (const std::exception& e) {
        LOGE("Exception during OTR generation: %s", e.what());
        return false;
    } catch (...) {
        LOGE("Unknown error during OTR generation");
        return false;
    }
}