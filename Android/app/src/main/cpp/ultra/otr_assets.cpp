#include "otr_assets.hpp"
#include <fstream>
#include <vector>
#include <cstdint>
#include <iostream>

// ------------------------------
// Helper to load a file and convert to a constexpr-like array at build time
// ------------------------------
namespace {

std::vector<uint8_t> readFileBytes(const char* path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) {
        std::cerr << "Failed to open file: " << path << std::endl;
        return {};
    }
    std::vector<uint8_t> buffer((std::istreambuf_iterator<char>(file)),
                                std::istreambuf_iterator<char>());
    return buffer;
}

// Macro to generate array and size
#define EMBED_YAML_ARRAY(NAME, PATH)                 \
    static std::vector<uint8_t> NAME##_vec = readFileBytes(PATH); \
    const uint8_t NAME[] = {                         \
        NAME##_vec.empty() ? 0 : NAME##_vec[0]      /* placeholder for static array */ \
    };                                               \
    const size_t NAME##_size = NAME##_vec.size();

} // anonymous namespace

// ------------------------------
// Embed the YAML files
// ------------------------------
// Update paths relative to CMake or source root
static const char* palYamlPath = "Android/app/src/main/assets/otr_yaml/decompressed.pal.yaml";
static const char* usYamlPath  = "Android/app/src/main/assets/otr_yaml/decompressed.us.v10.yaml";

// Load files into static byte arrays
std::vector<uint8_t> embedded_pal_vector = readFileBytes(palYamlPath);
std::vector<uint8_t> embedded_us_vector  = readFileBytes(usYamlPath);

const uint8_t embedded_pal_yaml[] = {
    embedded_pal_vector.empty() ? 0 : embedded_pal_vector[0]  // Placeholder for build-time embedding
};
const size_t embedded_pal_size = embedded_pal_vector.size();

const uint8_t embedded_us_yaml[] = {
    embedded_us_vector.empty() ? 0 : embedded_us_vector[0]  // Placeholder for build-time embedding
};
const size_t embedded_us_size = embedded_us_vector.size();