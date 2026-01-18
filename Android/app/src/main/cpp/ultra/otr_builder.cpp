#include "otr_builder.h"
#include "otr_generator.h"
#include <android/log.h>
#define LOG_TAG "OTR_BUILDER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

namespace OTRBuilder {

bool buildBKOTR(const uint8_t* romData, size_t romSize, const char* yamlData, size_t yamlSize, std::vector<uint8_t>& outOTR){
    outOTR.clear();
    if(!romData||romSize==0||!yamlData||yamlSize==0){ LOGE("Invalid input"); return false; }
    OTRGenerator gen;
    if(!gen.generateOTR(romData, romSize, yamlData, yamlSize, outOTR)){ LOGE("OTR generation failed"); return false; }
    LOGI("OTR generated, size=%zu", outOTR.size());
    return true;
}

bool buildOTRForROM(AAssetManager* mgr, const uint8_t* romData, size_t romSize, std::vector<uint8_t>& outOTR){
    if(!mgr||!romData||romSize==0){ LOGE("Invalid input"); return false; }
    OTRGenerator::RomInfo info{};
    if(!OTRGenerator::detectRomVersion(romData, romSize, info)){ LOGE("ROM version detection failed"); return false; }
    std::string yamlPath;
    if(info.version=="USv1.0") yamlPath="otr_yaml/decompressed.us.v10.yaml";
    else if(info.version=="PAL") yamlPath="otr_yaml/decompressed.pal.yaml";
    else { LOGE("Unsupported ROM version"); return false; }
    std::vector<uint8_t> yamlBuf = OTRGenerator::loadYAMLAsset(mgr, yamlPath.c_str());
    if(yamlBuf.empty()){ LOGE("Failed to load YAML"); return false; }
    return buildBKOTR(romData, romSize, reinterpret_cast<const char*>(yamlBuf.data()), yamlBuf.size(), outOTR);
}

} // namespace OTRBuilder