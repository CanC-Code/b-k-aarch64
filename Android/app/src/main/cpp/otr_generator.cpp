#include "otr_generator.hpp"
#include <cstring>
#include <algorithm>
#include <android/log.h>

#define LOG_TAG "OTRGenerator"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

void OTRGenerator::loadYAML(const char* key, const uint8_t* data, size_t size) {
    if (!key || !data || size == 0) return;
    YAMLData y;
    y.bytes.assign(data, data + size);
    yamlMap_[key] = std::move(y);
    LOGI("YAML loaded for key '%s', size=%zu bytes", key, size);
}

bool OTRGenerator::generate(const char* key, std::vector<uint8_t>& out) {
    if (!key) return false;
    auto it = yamlMap_.find(key);
    if (it == yamlMap_.end()) {
        LOGE("No YAML loaded for key '%s'", key);
        return false;
    }

    generateInternal(it->second, out);
    generatedOTR_[key] = out;
    return true;
}

float OTRGenerator::getProgress() const {
    return progress_;
}

// --- Internal OTR generation ---
// Simple mock: concatenates YAML bytes to simulate OTR
void OTRGenerator::generateInternal(const YAMLData& yaml, std::vector<uint8_t>& out) {
    out.clear();
    size_t total = yaml.bytes.size();
    out.reserve(total);

    for (size_t i = 0; i < total; ++i) {
        out.push_back(yaml.bytes[i]);
        progress_ = static_cast<float>(i) / total;
    }

    progress_ = 1.0f;
    LOGI("OTR generated, size=%zu bytes", out.size());
}