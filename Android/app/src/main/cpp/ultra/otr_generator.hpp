#pragma once

#include <vector>
#include <string>
#include <cstdint>
#include <functional>
#include <android/log.h>

#ifndef LOG_TAG
#define LOG_TAG "OTR_GEN"
#endif
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Minimal stub of OTRGenerator
class OTRGenerator {
public:
    OTRGenerator() = default;

    // Load in-memory YAML
    void loadEmbeddedYAML(const std::string& name, const uint8_t* data, size_t size) {
        LOGI("Loaded YAML: %s (%zu bytes)", name.c_str(), size);
        yamlData_.emplace_back(name, std::vector<uint8_t>(data, data + size));
    }

    // Generate OTR; calls progress callback
    void generate(const std::function<void(float)>& progressCallback) {
        LOGI("Starting OTR generation...");
        for (int i = 0; i <= 100; ++i) {
            progressCallback(i / 100.0f);
        }

        // Minimal fake data
        output_.resize(1024, 0xAA);
        LOGI("OTR generation finished (size=%zu)", output_.size());
    }

    const std::vector<uint8_t>& getData() const { return output_; }

private:
    std::vector<std::pair<std::string, std::vector<uint8_t>>> yamlData_;
    std::vector<uint8_t> output_;
};