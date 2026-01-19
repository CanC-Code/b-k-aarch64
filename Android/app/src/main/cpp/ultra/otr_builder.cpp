#include "otr_generator.hpp"
#include "otr_assets.hpp"
#include <vector>
#include <cstdint>

bool generateOTRFromROM(const uint8_t* romData, size_t romSize, float& outProgress) {
    OTRGenerator generator;

    // Load embedded YAML assets
    generator.loadEmbeddedYAML("decompressed.pal.yaml", embedded_pal_yaml, embedded_pal_yaml_size);
    generator.loadEmbeddedYAML("decompressed.us.v10.yaml", embedded_us_yaml, embedded_us_yaml_size);

    // Generate OTR directly from ROM
    bool success = generator.generate(
        romData,
        romSize,
        [&](float progress) { outProgress = progress; }
    );

    return success;
}