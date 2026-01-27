#include "otr_builder.h"
#include "assets_manifest.h"
#include "../tools/rare_decompression.h"
#include <vector>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <android/log.h> // Added for debugging

#define LOG_TAG "OTR_BUILDER"
#define LOGD(...) __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, const char* outDirPath) {
    mkdir(outDirPath, 0777);

    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));

    LOGD("Starting OTR generation for %u entries", header->entryCount);

    for (uint32_t i = 0; i < header->entryCount; i++) {
        AssetEntry& asset = entries[i];
        if (asset.type == ASSET_TYPE_SKIP) continue;

        lseek(romFd, asset.romOffset, SEEK_SET);
        std::vector<uint8_t> comp(asset.compSize);
        ssize_t bytesRead = read(romFd, comp.data(), asset.compSize);

        if (bytesRead <= 0) {
            LOGE("Failed to read asset: %s", asset.name);
            continue;
        }

        uint32_t actualDecompSize = 0;
        uint8_t* decomp = decompress_rare_asset(comp.data(), (uint32_t)comp.size(), &actualDecompSize);

        if (decomp) {
            char path[512];
            snprintf(path, sizeof(path), "%s/%s", outDirPath, asset.name);

            int out = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0666);
            if (out != -1) {
                write(out, decomp, actualDecompSize);
                close(out);
            }
            free(decomp);
        } else {
            // This is likely where your 25% hang is hiding
            LOGE("Decompression failed for: %s (Type: %d)", asset.name, asset.type);
        }

        // Progress Callback - Throttle updates to avoid flooding UI thread
        if (env && activity && progressMid && (i % 5 == 0 || i == header->entryCount - 1)) {
            int percent = (int)((float)(i + 1) / header->entryCount * 100.0f);
            jstring jName = env->NewStringUTF(asset.name);
            env->CallVoidMethod(activity, progressMid, percent, jName);
            env->DeleteLocalRef(jName);
        }
    }
    LOGD("OTR Generation Complete");
}
