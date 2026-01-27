// Android/app/src/main/cpp/ultra/otr_builder.cpp
#include "otr_builder.h"
#include "assets_manifest.h"
#include "rare_decompression.h"
#include <vector>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <sys/stat.h>
#include <android/log.h>

#define LOG_TAG "OTR_BUILDER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

void run_otr_generation(int romFd, uint8_t* manifestPtr, const char* outDirPath) {
    if (!manifestPtr || !outDirPath) {
        LOGE("Invalid manifest or output path provided.");
        return;
    }

    // Create the output directory if it doesn't exist
    mkdir(outDirPath, 0777);

    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));

    LOGI("Starting OTR generation for %u assets...", header->entryCount);

    for (uint32_t i = 0; i < header->entryCount; i++) {
        AssetEntry& asset = entries[i];

        // Mirroring generate_assets_enums.py: Skip specific types (Midi, etc.)
        if (asset.type == ASSET_TYPE_SKIP) {
            continue;
        }

        // 1. Move to ROM position (Splat logic replacement)
        if (lseek(romFd, asset.romOffset, SEEK_SET) == (off_t)-1) {
            LOGE("Failed to seek to offset 0x%X for asset %s", asset.romOffset, asset.name);
            continue;
        }

        // 2. Read compressed data block
        std::vector<uint8_t> compBuffer(asset.compSize);
        ssize_t bytesRead = read(romFd, compBuffer.data(), asset.compSize);
        
        if (bytesRead != (ssize_t)asset.compSize) {
            LOGE("Failed to read compressed data for %s", asset.name);
            continue;
        }

        // 3. Decompress (Rareunzip.py logic replacement)
        // Now using the updated signature with src_size safety
        uint32_t actualDecompSize = 0;
        uint8_t* decompData = decompress_rare_asset(compBuffer.data(), (uint32_t)compBuffer.size(), &actualDecompSize);

        if (decompData) {
            // 4. Write to Internal Storage
            char fullPath[512];
            snprintf(fullPath, sizeof(fullPath), "%s/%s", outDirPath, asset.name);
            
            int outFd = open(fullPath, O_WRONLY | O_CREAT | O_TRUNC, 0666);
            if (outFd != -1) {
                write(outFd, decompData, actualDecompSize);
                close(outFd);
            } else {
                LOGE("Could not open file for writing: %s", fullPath);
            }

            // Important: decompress_rare_asset uses malloc
            free(decompData);
        } else {
            LOGE("Decompression failed for asset: %s (ID: 0x%X)", asset.name, asset.uid);
        }
        
        // Note: Progress reporting via JNI can be added here
    }

    LOGI("OTR generation complete.");
}
