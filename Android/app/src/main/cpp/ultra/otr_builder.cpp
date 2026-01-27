#include "otr_builder.h"
#include "assets_manifest.h"
#include "rare_decompression.h"
#include <vector>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h> // REQUIRED for O_WRONLY, O_CREAT
#include <stdio.h>
#include <stdlib.h>

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, const char* outDirPath) {
    mkdir(outDirPath, 0777);

    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));

    for (uint32_t i = 0; i < header->entryCount; i++) {
        AssetEntry& asset = entries[i];
        if (asset.type == ASSET_TYPE_SKIP) continue;

        lseek(romFd, asset.romOffset, SEEK_SET);
        std::vector<uint8_t> comp(asset.compSize);
        read(romFd, comp.data(), asset.compSize);

        uint32_t actualDecompSize = 0;
        // Adjusted to match your rare_decompression.h: uint8_t* (src, uint32_t* out_size)
        uint8_t* decomp = decompress_rare_asset(comp.data(), &actualDecompSize);

        if (decomp) {
            char path[512];
            snprintf(path, sizeof(path), "%s/%s", outDirPath, asset.name);
            int out = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0666);
            if (out != -1) {
                write(out, decomp, actualDecompSize);
                close(out);
            }
            free(decomp);
        }

        // Progress Callback
        if (env && activity && progressMid) {
            int percent = (int)((float)(i + 1) / header->entryCount * 100.0f);
            jstring jName = env->NewStringUTF(asset.name);
            env->CallVoidMethod(activity, progressMid, percent, jName);
            env->DeleteLocalRef(jName);
        }
    }
}
