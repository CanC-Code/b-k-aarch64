#include "otr_generator.hpp"
#include <stdexcept>
#include <cstring>

bool OTRGenerator::detectRomVersion(const uint8_t* romData, size_t romSize, RomInfo& outInfo) {
    if (!romData || romSize < 4) return false;

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

bool OTRGenerator::generate(
        const uint8_t* romData,
        size_t romSize,
        const std::vector<std::pair<std::string, std::vector<uint8_t>>>& yamlAssets
) {
    if (!romData || romSize == 0 || yamlAssets.empty()) {
        LOGE("Invalid ROM or YAML assets");
        return false;
    }

    try {
        outOTR.clear();
        size_t totalSteps = 100 * yamlAssets.size(); // more granular progress
        size_t stepCounter = 0;

        for (const auto& assetPair : yamlAssets) {
            const auto& yamlData = assetPair.second;
            if (yamlData.empty()) continue;

            size_t chunkROM = romSize / 100;
            size_t chunkYAML = yamlData.size() / 100;

            for (size_t i = 0; i < 100; ++i) {
                // ROM chunk
                size_t romStart = i * chunkROM;
                size_t romEnd = (i == 99) ? romSize : romStart + chunkROM;
                outOTR.insert(outOTR.end(), romData + romStart, romData + romEnd);

                // YAML chunk
                size_t yamlStart = i * chunkYAML;
                size_t yamlEnd = (i == 99) ? yamlData.size() : yamlStart + chunkYAML;
                outOTR.insert(outOTR.end(), yamlData.data() + yamlStart, yamlData.data() + yamlEnd);

                reportProgress(static_cast<float>(++stepCounter) / static_cast<float>(totalSteps));
            }
        }

        reportProgress(1.0f);
        LOGI("OTR generation complete: %zu bytes", outOTR.size());
        return true;

    } catch (const std::exception& e) {
        LOGE("Exception during OTR generation: %s", e.what());
        return false;
    } catch (...) {
        LOGE("Unknown exception during OTR generation");
        return false;
    }
}