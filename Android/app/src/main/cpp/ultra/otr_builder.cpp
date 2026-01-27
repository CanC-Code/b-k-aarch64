// Android/app/src/main/cpp/ultra/otr_builder.cpp
#include "otr_builder.h"
#include "assets_manifest.h"
#include "rare_decompression.h"
#include <vector>
#include <fcntl.h>
#include <unistd.h>
#include <android/log.h>

void run_native_otr_extraction(JNIEnv* env, jobject activity, int romFd, 
                               uint8_t* manifestPtr, size_t manifestSize, 
                               const char* outDirPath) {
    
    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));

    jclass activityClass = env->GetObjectClass(activity);
    jmethodID updateMethod = env->GetMethodID(activityClass, "updateOtrProgress", "(ILjava/lang/String;)V");

    for (uint32_t i = 0; i < header->entryCount; i++) {
        AssetEntry& asset = entries[i];
        
        // Skip metadata/midis if defined in manifest as skip
        if (asset.type == ASSET_TYPE_SKIP) continue;

        // 1. Seek and Read from ROM
        lseek(romFd, asset.romOffset, SEEK_SET);
        std::vector<uint8_t> compBuffer(asset.compSize);
        read(romFd, compBuffer.data(), asset.compSize);

        // 2. Decompress (Ported from rareunzip.py logic)
        uint32_t actualDecompSize = 0;
        uint8_t* decompData = decompress_rare_asset(compBuffer.data(), &actualDecompSize);

        if (decompData) {
            // 3. Write to Android Internal Storage
            std::string outPath = std::string(outDirPath) + "/" + asset.name;
            int outFd = open(outPath.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0666);
            write(outFd, decompData, actualDecompSize);
            close(outFd);
            free(decompData);
        }

        // Update UI
        jstring jName = env->NewStringUTF(asset.name);
        env->CallVoidMethod(activity, updateMethod, i, jName);
        env->DeleteLocalRef(jName);
    }
}
