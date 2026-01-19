#pragma once
#include <vector>
#include <cstdint>
#include <string>
#include <unordered_map>

class OTRGenerator {
public:
    OTRGenerator() = default;

    // Load YAML bytes for a given version key
    void loadYAML(const char* key, const uint8_t* data, size_t size);

    // Generate the OTR array for a given version key
    bool generate(const char* key, std::vector<uint8_t>& out);

    // Optional: get progress [0.0, 1.0]
    float getProgress() const;

private:
    struct YAMLData {
        std::vector<uint8_t> bytes;
    };

    std::unordered_map<std::string, YAMLData> yamlMap_;
    std::unordered_map<std::string, std::vector<uint8_t>> generatedOTR_;
    mutable float progress_ = 0.0f;

    void generateInternal(const YAMLData& yaml, std::vector<uint8_t>& out);
};