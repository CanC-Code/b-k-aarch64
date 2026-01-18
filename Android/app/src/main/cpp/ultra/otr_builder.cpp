// File: otr_builder.cpp
// Purpose: Deterministic ROM → OTR loader (inline, no fictional abstractions)

#include <cstdint>
#include <cstddef>
#include <vector>
#include <string>
#include <unordered_map>
#include <fstream>
#include <sstream>

#include <openssl/sha.h>

#include <android/log.h>

#define LOG_TAG "OTR_BUILDER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// ---------------------------------------------------------------------
// Known ROM SHA1 → OTR BIN filename
// ---------------------------------------------------------------------
static const std::unordered_map<std::string, std::string> g_romToBin = {
    // Banjo-Kazooie US v1.0
    { "1fb13cad402518d3ae9a8dc4b52c5c54b2a4adc7", "us_v10.bin" },

    // Banjo-Kazooie PAL
    // Fill in real SHA1 when verified
    // { "<PAL_SHA1>", "pal.bin" },
};

// ---------------------------------------------------------------------
// Compute SHA1 hex string
// ---------------------------------------------------------------------
static std::string sha1Hex(const uint8_t* data, size_t size) {
    uint8_t hash[SHA_DIGEST_LENGTH];
    SHA1(data, size, hash);

    static const char hex[] = "0123456789abcdef";
    std::string out;
    out.reserve(SHA_DIGEST_LENGTH * 2);

    for (int i = 0; i < SHA_DIGEST_LENGTH; ++i) {
        out.push_back(hex[(hash[i] >> 4) & 0xF]);
        out.push_back(hex[hash[i] & 0xF]);
    }

    return out;
}

// ---------------------------------------------------------------------
// Load entire file into vector
// ---------------------------------------------------------------------
static bool loadFile(
    const std::string& path,
    std::vector<uint8_t>& outData
) {
    std::ifstream f(path, std::ios::binary);
    if (!f.is_open()) {
        LOGE("Failed to open OTR BIN: %s", path.c_str());
        return false;
    }

    f.seekg(0, std::ios::end);
    size_t size = static_cast<size_t>(f.tellg());
    f.seekg(0, std::ios::beg);

    if (size == 0) {
        LOGE("OTR BIN empty: %s", path.c_str());
        return false;
    }

    outData.resize(size);
    f.read(reinterpret_cast<char*>(outData.data()), size);
    return true;
}

// ---------------------------------------------------------------------
// Public API: buildBKOTR
// ---------------------------------------------------------------------
bool buildBKOTR(
    const uint8_t* romData,
    size_t romSize,
    std::vector<uint8_t>& outOTR
) {
    outOTR.clear();

    if (!romData || romSize == 0) {
        LOGE("Invalid ROM input");
        return false;
    }

    // --- Detect ROM via SHA1 ---
    std::string sha1 = sha1Hex(romData, romSize);
    LOGI("ROM SHA1: %s", sha1.c_str());

    auto it = g_romToBin.find(sha1);
    if (it == g_romToBin.end()) {
        LOGE("Unsupported ROM SHA1");
        return false;
    }

    // --- Resolve OTR BIN path ---
    // APK packs these under:
    // Android/app/src/main/assets/otr_bins/
    const std::string binPath =
        "/android_asset/otr_bins/" + it->second;

    LOGI("Selected OTR BIN: %s", binPath.c_str());

    // --- Load BIN into memory ---
    if (!loadFile(binPath, outOTR)) {
        LOGE("Failed to load OTR BIN");
        outOTR.clear();
        return false;
    }

    LOGI("OTR loaded successfully (%zu bytes)", outOTR.size());
    return true;
}