#pragma once
#include <vector>
#include <android/asset_manager.h>

std::vector<uint8_t> readAsset(AAssetManager* mgr, const char* path);