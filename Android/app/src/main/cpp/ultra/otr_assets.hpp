#pragma once
#include <cstddef>
#include <cstdint>

// ------------------------------
// Embedded OTR YAML assets
// ------------------------------

// PAL YAML
extern const uint8_t embedded_pal_yaml[];
extern const size_t embedded_pal_size;

// US YAML
extern const uint8_t embedded_us_yaml[];
extern const size_t embedded_us_size;

// ------------------------------
// Helper function to access as string
// ------------------------------
inline const char* getEmbeddedPalYamlAsCString() {
    return reinterpret_cast<const char*>(embedded_pal_yaml);
}

inline const char* getEmbeddedUsYamlAsCString() {
    return reinterpret_cast<const char*>(embedded_us_yaml);
}

// Returns size
inline size_t getEmbeddedPalYamlSize() {
    return embedded_pal_size;
}

inline size_t getEmbeddedUsYamlSize() {
    return embedded_us_size;
}