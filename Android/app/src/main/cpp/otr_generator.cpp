#include "otr_generator.hpp"
#include <android/asset_manager.h>
#include <android/log.h>
#include <fstream>

#define LOG_TAG "OTR"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

bool GenerateOTR(
    const uint8_t* romData,
    size_t romSize,
    AAssetManager* assetManager,
    const char* yamlAssetPath,
    const char* outputDir,
    std::function<void(float)> progressCallback
) {
    progressCallback(0.05f);

    AAsset* yamlAsset = AAssetManager_open(
            assetManager,
            yamlAssetPath,
            AASSET_MODE_BUFFER);

    if (!yamlAsset) {
        LOGE("Failed to open YAML asset: %s", yamlAssetPath);
        return false;
    }

    const size_t yamlSize = AAsset_getLength(yamlAsset);
    std::vector<uint8_t> yamlData(yamlSize);
    AAsset_read(yamlAsset, yamlData.data(), yamlSize);
    AAsset_close(yamlAsset);

    progressCallback(0.2f);

    // Write ROM to temp file
    std::string romPath = std::string(outputDir) + "/input.rom";
    std::ofstream romFile(romPath, std::ios::binary);
    romFile.write(reinterpret_cast<const char*>(romData), romSize);
    romFile.close();

    progressCallback(0.4f);

    // TODO: Hook real OTR generation here
    // This is where your existing OTR toolchain logic goes

    std::string otrPath = std::string(outputDir) + "/game.otr";
    std::ofstream dummy(otrPath, std::ios::binary);
    dummy << "OTR_PLACEHOLDER";
    dummy.close();

    progressCallback(1.0f);
    LOGI("OTR generated at %s", otrPath.c_str());

    return true;
}