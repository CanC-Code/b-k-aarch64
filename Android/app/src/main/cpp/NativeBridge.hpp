// File: Android/app/src/main/cpp/NativeBridge.hpp
#pragma once

#include <android/asset_manager.h>
#include <vector>
#include <cstdint>

// Reads an asset into a vector of bytes
std::vector<uint8_t> readAsset(AAssetManager* mgr, const char* path);