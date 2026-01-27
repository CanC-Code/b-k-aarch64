#include "otr_builder.h"
#include "assets_manifest.h"
#include "../tools/rare_decompression.h"
#include <vector>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <android/log.h>

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

        // --- UI UPDATE: Send current filename before starting work ---
        // This ensures the UI tells us exactly what it's trying to do
        if (env && activity && progressMid) {
            int percent = (int)((float)(i) / header->entryCount * 100.0f);
            jstring jName = env->NewStringUTF(asset.name);
            env->CallVoidMethod(activity, progressMid, percent, jName);
            env->DeleteLocalRef(jName);
        }

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
            // Log the failure clearly in Logcat
            LOGE("Decompression failed for: %s (Offset: 0x%X, Size: %u)", 
                 asset.name, asset.romOffset, asset.compSize);
        }
    }
    
    // Final 100% callback
    if (env && activity && progressMid) {
        jstring finishedMsg = env->NewStringUTF("Complete");
        env->CallVoidMethod(activity, progressMid, 100, finishedMsg);
        env->DeleteLocalRef(finishedMsg);
    }
    
    LOGD("OTR Generation Complete");
}
