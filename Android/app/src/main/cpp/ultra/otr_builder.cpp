#include "otr_builder.h"
#include "rare_decompression.h"
#include <android/log.h>
#include <unistd.h>
#include <vector>
#include <string>

#define LOG_TAG "BKA_OTR"

// Ensure struct is packed to exactly 48 bytes
#pragma pack(push, 1)
struct ManifestEntry {
    uint32_t offset;
    uint32_t size;
    char name[32];
    char type[8];
};
#pragma pack(pop)

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, uint32_t manifestSize, 
                                           const char* outDirPath) {

    uint32_t entryCount = *(uint32_t*)manifestPtr;
    ManifestEntry* entries = (ManifestEntry*)(manifestPtr + 4);

    for (uint32_t i = 0; i < entryCount; i++) {
        ManifestEntry& current = entries[i];

        // 1. Skip invalid sizes
        if (current.size == 0) continue;

        // 2. Read exact bytes from ROM
        std::vector<uint8_t> romBuffer(current.size);
        ssize_t bytesRead = pread(romFd, romBuffer.data(), current.size, current.offset);

        if (bytesRead > 0) {
            uint32_t decompressedSize = 0;
            // 3. Decompress using the Rare tool
            uint8_t* out = decompress_rare_asset(romBuffer.data(), (uint32_t)bytesRead, &decompressedSize);
            
            if (out) {
                // TODO: Save to disk in outDirPath
                // e.g., write_to_file(outDirPath, current.name, out, decompressedSize);
                free(out);
            } else {
                // Fallback: This is likely a raw asset (Midi, etc)
                // write_to_file(outDirPath, current.name, romBuffer.data(), bytesRead);
            }
        }

        // 4. Reporting: This is why your progress was 0% before. 
        // We report every asset name back to Java.
        if (i % 5 == 0 || i == entryCount - 1) {
            int percent = (int)((i * 100) / entryCount);
            jstring jName = env->NewStringUTF(current.name);
            env->CallVoidMethod(activity, progressMid, percent, jName);
            env->DeleteLocalRef(jName);
        }
    }
}
