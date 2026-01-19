#pragma once

#include <android/asset_manager.h>
#include <android/asset_manager_jni.h>
#include <vector>
#include <string>
#include <unordered_map>

class OTRGenerator {
public:
    explicit OTRGenerator(AAssetManager* mgr) : assetManager(mgr) {}

    // Load YAML data from memory buffer
    void loadYAML(const std::string& name, const uint8_t* data, size_t size) {
        yamlData[name] = std::vector<uint8_t>(data, data + size);
    }

    // Generate OTR in-memory representation (stub example)
    bool generate(const std::string& name, std::vector<uint8_t>& outData) {
        auto it = yamlData.find(name);
        if (it == yamlData.end()) return false;

        // TODO: replace this with real OTR generation logic
        outData = it->second;
        return true;
    }

private:
    AAssetManager* assetManager;
    std::unordered_map<std::string, std::vector<uint8_t>> yamlData;
};