#include "otr_builder.h"
#include "assets_manifest.h"
#include "../tools/rare_decompression.h"
#include <vector>
#include <thread>
#include <mutex>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>

std::mutex progress_mutex;

void process_asset(int romFd, AssetEntry& asset, const char* outDirPath) {
    char path[512];
    snprintf(path, sizeof(path), "%s/%s", outDirPath, asset.name);

    // RESUME LOGIC: Check if file already exists
    struct stat st;
    if (stat(path, &st) == 0) return; 

    // Read and Decompress
    std::vector<uint8_t> comp(asset.compSize);
    // Use pread for thread-safe reading without lseek
    pread(romFd, comp.data(), asset.compSize, asset.romOffset);

    uint32_t outSize = 0;
    uint8_t* decomp = decompress_rare_asset(comp.data(), asset.compSize, &outSize);

    if (decomp) {
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
    mkdir(outDirPath, 0777);
    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));

    const int numThreads = 4;
    for (uint32_t i = 0; i < header->entryCount; i += numThreads) {
        std::vector<std::thread> workers;
        for (int t = 0; t < numThreads && (i + t) < header->entryCount; t++) {
            AssetEntry& asset = entries[i + t];
            if (asset.type == ASSET_TYPE_SKIP) continue;

            workers.emplace_back(process_asset, romFd, std::ref(asset), outDirPath);
        }

        for (auto& w : workers) w.join();

        // Update UI every batch
        if (env && activity && progressMid) {
            int percent = (int)((float)(i) / header->entryCount * 100.0f);
            jstring jName = env->NewStringUTF(entries[i].name);
            env->CallVoidMethod(activity, progressMid, percent, jName);
            env->DeleteLocalRef(jName);
        }
    }
}
