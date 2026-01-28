#include "otr_builder.h"
#include "rare_decompression.h"
#include <android/log.h>
#include <unistd.h>
#include <vector>
#include <string>

#define LOG_TAG "OTR_BUILDER"

// MUST match the Python struct.pack('<II32s8s', ...)
#pragma pack(push, 1) // Ensure no compiler padding
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

    if (manifestSize < 4) return;

    // Read header (4 bytes)
    uint32_t entryCount = *(uint32_t*)manifestPtr;
    ManifestEntry* entries = (ManifestEntry*)(manifestPtr + 4);

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Starting extraction: %u assets", entryCount);

    for (uint32_t i = 0; i < entryCount; i++) {
        ManifestEntry& current = entries[i];
        
        // Skip assets with 0 size or logical errors
        if (current.size == 0 || current.size > 20 * 1024 * 1024) {
            continue; 
        }

        std::vector<uint8_t> buffer(current.size);
        ssize_t bytesRead = pread(romFd, buffer.data(), current.size, current.offset);

        if (bytesRead > 0) {
            uint32_t decompSize = 0;
            // The Rare Decompression tool needs the exact size to find the Zlib stream
            uint8_t* out = decompress_rare_asset(buffer.data(), (uint32_t)bytesRead, &decompSize);
            
            if (out) {
                // Asset is decompressed. Here you would write to OTR file.
                // For now, we just ensure the loop keeps moving to move progress.
                free(out);
            }
        }

        // Update UI every 5 assets to keep the progress bar fluid
        if (i % 5 == 0 || i == entryCount - 1) {
            int percent = (int)((i * 100) / entryCount);
            jstring jName = env->NewStringUTF(current.name);
            env->CallVoidMethod(activity, progressMid, percent, jName);
            env->DeleteLocalRef(jName);
        }
    }

    // Final UI update to 100%
    jstring finishMsg = env->NewStringUTF("Done");
    env->CallVoidMethod(activity, progressMid, 100, finishMsg);
    env->DeleteLocalRef(finishMsg);
}
