#pragma once

#include <cstdint>

// ---------------------------------------------
// Runtime OTR/YAML system
// ---------------------------------------------
// YAML is selected and loaded at runtime based
// on the detected ROM version.
//
// These symbols are intentionally NOT defined.
// Any attempt to use them indicates a bug.
// ---------------------------------------------

static inline const uint8_t* getEmbeddedYAML(const char*) {
    return nullptr;
}

static inline size_t getEmbeddedYAMLSize(const char*) {
    return 0;
}