#include "otr_generator.hpp"
#include <vector>
#include <cstdint>

bool buildOTR(const std::vector<uint8_t>& palData, const std::vector<uint8_t>& usData,
              std::vector<uint8_t>& outPal, std::vector<uint8_t>& outUS)
{
    OTRGenerator generator;

    generator.loadYAML("pal", palData.data(), palData.size());
    generator.loadYAML("us.v10", usData.data(), usData.size());

    bool success1 = generator.generate("pal", outPal);
    bool success2 = generator.generate("us.v10", outUS);

    return success1 && success2;
}