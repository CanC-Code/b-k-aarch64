#include "otr_builder.h"
#include "assets_manifest.h"
#include "../tools/rare_decompression.h" // Ensure path is correct
#include <vector>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, const char* outDirPath) {
    // Create the output directory
    mkdir(outDirPath, 0777);

    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));

    for (uint32_t i = 0; i < header->entryCount; i++) {
        AssetEntry& asset = entries[i];
        if (asset.type == ASSET_TYPE_SKIP) continue;

        // 1. Seek and Read compressed data from ROM
        lseek(romFd, asset.romOffset, SEEK_SET);
        std::vector<uint8_t> comp(asset.compSize);
        read(romFd, comp.data(), asset.compSize);

        uint32_t actualDecompSize = 0;
        
        /**
         * FIXED: Now passing 3 arguments to match rare_decompression.h
         * 1. comp.data()     -> The compressed buffer
         * 2. asset.compSize  -> The size of the compressed buffer (Safety check)
         * 3. &actualDecompSize -> Where the function writes the final size
         */
        uint8_t* decomp = decompress_rare_asset(comp.data(), asset.compSize, &actualDecompSize);

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

        // 2. Progress Callback
        if (env && activity && progressMid) {
            int percent = (int)((float)(i + 1) / header->entryCount * 100.0f);
            
            // Note: Ensure your Java/Kotlin updateProgress signature matches (I, Ljava/lang/String;)V
            jstring jName = env->NewStringUTF(asset.name);
            env->CallVoidMethod(activity, progressMid, percent, jName);
            env->DeleteLocalRef(jName);
        }
    }
}
