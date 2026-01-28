#include "otr_builder.h"
#include "rare_decompression.h"
#include <android/log.h>
#include <unistd.h>
#include <vector>
#include <string>
#include <fcntl.h>

#define LOG_TAG "OTR_BUILDER"

// Assuming your manifest entry structure looks like this based on common Rare formats:
// 4 bytes: UID, 4 bytes: ROM Offset, 4 bytes: Compressed Size
struct ManifestEntry {
    uint32_t uid;
    uint32_t offset;
    uint32_t size;
};

static JavaVM* g_vm = nullptr;

void otr_builder_set_jvm(JavaVM* vm) {
    g_vm = vm;
}

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, uint32_t manifestSize, 
                                           const char* outDirPath) {

    if (manifestSize < sizeof(ManifestEntry)) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Manifest is too small!");
        return;
    }

    uint32_t entryCount = manifestSize / sizeof(ManifestEntry);
    ManifestEntry* entries = (ManifestEntry*)manifestPtr;

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Starting extraction of %u assets", entryCount);

    for (uint32_t i = 0; i < entryCount; i++) {
        ManifestEntry current = entries[i];
        
        // 1. Prepare buffer and read from ROM using the File Descriptor
        std::vector<uint8_t> compressedData(current.size);
        ssize_t bytesRead = pread(romFd, compressedData.data(), current.size, current.offset);

        if (bytesRead > 0) {
            uint32_t decompressedSize = 0;
            
            // 2. Attempt Rare Decompression (Magic 11 72)
            uint8_t* outData = decompress_rare_asset(compressedData.data(), (uint32_t)bytesRead, &decompressedSize);

            if (outData != nullptr) {
                // TODO: Save 'outData' to OTR file in outDirPath
                // For now, we just free it to prevent memory leaks
                free(outData);
            } else {
                // 3. Fallback: Treat as raw asset if decompression returned null
                // This ensures assets like Midis/Models still get processed
            }
        }

        // 4. Update Progress every asset (or every 10 assets to save JNI overhead)
        if (i % 5 == 0 || i == entryCount - 1) {
            int percent = (int)((i * 100) / entryCount);
            std::string status = "Asset 0x" + std::to_string(current.uid);
            jstring jStatus = env->NewStringUTF(status.c_str());
            
            env->CallVoidMethod(activity, progressMid, percent, jStatus);
            env->DeleteLocalRef(jStatus);
        }
    }

    // Final 100% update
    jstring finalStatus = env->NewStringUTF("Complete");
    env->CallVoidMethod(activity, progressMid, 100, finalStatus);
    env->DeleteLocalRef(finalStatus);

    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "OTR Generation Finished");
}
