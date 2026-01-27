#include "otr_builder.h"
#include "assets_manifest.h"
#include "rare_decompression.h"
#include <vector>
#include <unistd.h>
#include <sys/stat.h>

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, const char* outDirPath) {
    mkdir(outDirPath, 0777);

    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));

    for (uint32_t i = 0; i < header->entryCount; i++) {
        AssetEntry& asset = entries[i];
        if (asset.type == ASSET_TYPE_SKIP) continue;

        // Seek and Read ROM
        lseek(romFd, asset.romOffset, SEEK_SET);
        std::vector<uint8_t> comp(asset.compSize);
        read(romFd, comp.data(), asset.compSize);

        // Decompress
        uint32_t decompSize = 0;
        uint8_t* decomp = decompress_rare_asset(comp.data(), (uint32_t)comp.size(), &decompSize);

        if (decomp) {
            char path[512];
            snprintf(path, sizeof(path), "%s/%s", outDirPath, asset.name);
            int out = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0666);
            write(out, decomp, decompSize);
            close(out);
            free(decomp);
        }

        // --- UI CALLBACK ---
        int percent = (int)((float)i / header->entryCount * 100.0f);
        jstring jName = env->NewStringUTF(asset.name);
        env->CallVoidMethod(activity, progressMid, percent, jName);
        env->DeleteLocalRef(jName);
    }
}
