#include "otr_builder.h"
#include "assets_manifest.h"
#include "../tools/rare_decompression.h"
#include <vector>
#include <thread>
#include <mutex>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <android/log.h>

#define LOG_TAG "OTR_BUILDER"
#define LOGD(...) __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, __VA_ARGS__)

// Using a mutex to ensure thread-safe access to the ROM file descriptor if needed,
// though pread is generally thread-safe on Android/Linux.
std::mutex file_mutex;

void process_asset(int romFd, AssetEntry& asset, const char* outDirPath) {
    char path[512];
    snprintf(path, sizeof(path), "%s/%s", outDirPath, asset.name);

    // 1. RESUME LOGIC: Extremely fast check
    struct stat st;
    if (stat(path, &st) == 0 && st.st_size > 0) {
        return; 
    }

    // 2. Read compressed data (Thread-safe read)
    std::vector<uint8_t> comp(asset.compSize);
    ssize_t bytesRead = pread(romFd, comp.data(), asset.compSize, asset.romOffset);
    
    if (bytesRead < (ssize_t)asset.compSize) return;

    // 3. Decompress
    uint32_t outSize = 0;
    uint8_t* decomp = decompress_rare_asset(comp.data(), asset.compSize, &outSize);

    if (decomp) {
        // Ensure directory structure exists for the file if necessary
        // (Assuming flat structure or pre-created dirs for this manifest)
        int out = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0666);
        if (out != -1) {
            write(out, decomp, outSize);
            close(out);
        }
        free(decomp);
    }
}

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, const char* outDirPath) {
    // Ensure root output dir exists
    mkdir(outDirPath, 0777);
    
    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));

    LOGD("Starting Multithreaded OTR generation: %u entries", header->entryCount);

    // We process in batches of 4 to maximize CPU without overwhelming I/O
    const int batchSize = 4;
    
    for (uint32_t i = 0; i < header->entryCount; i += batchSize) {
        std::vector<std::thread> workers;

        for (int t = 0; t < batchSize && (i + t) < header->entryCount; t++) {
            AssetEntry& asset = entries[i + t];
            
            if (asset.type == ASSET_TYPE_SKIP) continue;

            workers.emplace_back(process_asset, romFd, std::ref(asset), outDirPath);
        }

        // Wait for this batch of 4 to finish
        for (auto& w : workers) {
            if (w.joinable()) w.join();
        }

        // 4. UI UPDATE: Done on the calling thread (safe for JNIEnv)
        if (env && activity && progressMid) {
            int percent = (int)((float)(i + 1) / header->entryCount * 100.0f);
            
            // Show the name of the last file in the batch
            jstring jName = env->NewStringUTF(entries[i].name);
            env->CallVoidMethod(activity, progressMid, percent, jName);
            env->DeleteLocalRef(jName);
        }
    }

    LOGD("OTR Generation Complete.");
}
