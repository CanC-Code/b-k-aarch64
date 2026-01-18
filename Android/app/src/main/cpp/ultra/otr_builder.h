// ultra/otr_builder.h
#pragma once
#include <vector>
#include <cstdint>

bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    std::vector<uint8_t>& outOTR
);