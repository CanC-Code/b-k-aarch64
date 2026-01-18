#include "otr_builder.h"
#include "otr_generator.h"
#include <android/log.h>
#include <vector>

#define LOG_TAG "OTR_BUILDER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

namespace OTRBuilder {

bool detectRomVersion(const uint8_t* romData, size_t romSize, RomInfo& outInfo) {
    if(!romData || romSize == 0) return false;
    std::string sha = OTRGenerator::sha1Hex(romData, romSize);
    if(sha=="1fb13cad402518d3ae9a8dc4b52c5c54b2a4adc7") outInfo.version="USv1.0";
    else return false;
    return true;
}

bool buildOTRForROM(AAssetManager* mgr,
                    const uint8_t* romData,
                    size_t romSize,
                    std::vector<uint8_t>& outOTR)
{
    if(!mgr || !romData || romSize==0) return false;
    RomInfo info{};
    if(!detectRomVersion(romData, romSize, info)) return false;

    const char* yamlData = nullptr;
    size_t yamlSize = 0;

    if(info.version=="USv1.0") {
        yamlData = OTRAssets::us_v10_yaml;
        yamlSize = OTRAssets::us_v10_size;
    } else {
        LOGE("Unsupported ROM version: %s", info.version.c_str());
        return false;
    }

    OTRGenerator gen;
    if(!gen.generateOTR(romData, romSize, yamlData, yamlSize, outOTR)) {
        LOGE("OTR generation failed");
        return false;
    }

    LOGI("OTR generated, size: %zu", outOTR.size());
    return true;
}

} // namespace OTRBuilder