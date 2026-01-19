#pragma once
#include <cstddef>
#include <cstdint>
#include "otr_generator.hpp"

// -----------------------------
// Embedded YAML assets
// -----------------------------
// These should match the files in:
// Android/app/src/main/assets/otr_yaml/

// Example: decompressed.pal.yaml
static const uint8_t embedded_pal_yaml[] = {
    #include "otr_yaml/decompressed.pal.yaml.inc"
};
static const size_t embedded_pal_size = sizeof(embedded_pal_yaml);

// Example: decompressed.us.v10.yaml
static const uint8_t embedded_us_yaml[] = {
    #include "otr_yaml/decompressed.us.v10.yaml.inc"
};
static const size_t embedded_us_size = sizeof(embedded_us_yaml);

// -----------------------------
// Array of embedded assets for OTRGenerator
// -----------------------------
static const EmbeddedAsset embedded_assets[] = {
    {"pal", embedded_pal_yaml, embedded_pal_size},
    {"us.v10", embedded_us_yaml, embedded_us_size}
};

static const size_t embedded_assets_count = sizeof(embedded_assets) / sizeof(embedded_assets[0]);