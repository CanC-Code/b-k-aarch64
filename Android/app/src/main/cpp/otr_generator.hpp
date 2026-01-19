// File: Android/app/src/main/cpp/otr_generator.hpp
// Purpose: OTR generation logic (header)

#pragma once

#include <vector>
#include <cstdint>

class OTRGenerator {
public:
    OTRGenerator() = default;
    ~OTRGenerator() = default;

    // Generate OTR data from palette and US YAML
    void generateOTR(const std::vector<uint8_t>& palData,
                     const std::vector<uint8_t>& usData);

    // Any other OTRGenerator methods...
};