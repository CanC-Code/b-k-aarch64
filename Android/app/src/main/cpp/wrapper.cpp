#include "otr_generator.hpp"
#include <android/asset_manager.h>
#include <android/log.h>

#define LOG_TAG "WRAPPER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" void generateOTRWrapper(AAssetManager* assetManager) {
    OTRGenerator generator(assetManager);

    auto palData = generator.readAsset(assetManager, "otr_yaml/decompressed.pal.yaml");
    auto usData  = generator.readAsset(assetManager, "otr_yaml/decompressed.us.v10.yaml");

    generator.loadYAML("pal", palData.data(), palData.size());
    generator.loadYAML("us.v10", usData.data(), usData.size());

    std::vector<uint8_t> outPal, outUS;
    if (generator.generate("pal", outPal))
        LOGI("PAL OTR generated, size: %zu", outPal.size());
    if (generator.generate("us.v10", outUS))
        LOGI("US OTR generated, size: %zu", outUS.size());
}