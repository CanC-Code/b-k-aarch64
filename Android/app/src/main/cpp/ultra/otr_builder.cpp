#include "otr_builder.h"
#include "rare_decompression.h"
#include <android/log.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdlib.h>
#include <sys/stat.h>

#define LOG_TAG "OtrBuilder"

// Helper to create directories for nested assets
void ensure_directories(const char* path) {
    char tmp[512];
    char* p = NULL;
    snprintf(tmp, sizeof(tmp), "%s", path);
    for (p = tmp + 1; *p; p++) {
        if (*p == '/') {
            *p = 0;
            mkdir(tmp, S_IRWXU);
            *p = '/';
        }
    }
}

extern "C" {
static JavaVM* g_vm = nullptr;
void otr_builder_set_jvm(JavaVM* vm) { g_vm = vm; }

void run_native_otr_generation_with_callback(JNIEnv* env, jobject callbackObj, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, uint32_t manifestSize, 
                                           const char* outDirPath) {

    uint32_t entryCount = manifestSize / 48;

    for (uint32_t i = 0; i < entryCount; i++) {
        if (env->PushLocalFrame(10) < 0) return;

        uint8_t* record = manifestPtr + (i * 48);
        
        // Convert Big Endian offsets from manifest
        uint32_t romOffset = __builtin_bswap32(*(uint32_t*)(record + 0));
        uint32_t fileSize  = __builtin_bswap32(*(uint32_t*)(record + 4));
        
        char fileName[33];
        memcpy(fileName, record + 8, 32);
        fileName[32] = '\0';

        char fullPath[512];
        snprintf(fullPath, sizeof(fullPath), "%s/%s", outDirPath, fileName);
        ensure_directories(fullPath);

        uint8_t* compressedBuffer = (uint8_t*)malloc(fileSize);
        if (compressedBuffer) {
            if (pread(romFd, compressedBuffer, fileSize, romOffset) == (ssize_t)fileSize) {
                uint32_t decompressedSize = 0;
                uint8_t* finalBuffer = decompress_rare_asset(compressedBuffer, fileSize, &decompressedSize);
                
                uint8_t* writePtr = (finalBuffer != nullptr) ? finalBuffer : compressedBuffer;
                uint32_t writeSize = (finalBuffer != nullptr) ? decompressedSize : fileSize;

                int outFd = open(fullPath, O_WRONLY | O_CREAT | O_TRUNC, 0666);
                if (outFd != -1) {
                    write(outFd, writePtr, writeSize);
                    close(outFd);
                }
                if (finalBuffer) free(finalBuffer);
            }
            free(compressedBuffer);
        }

        int percentage = (int)((i * 100) / entryCount);
        jstring jName = env->NewStringUTF(fileName);
        env->CallVoidMethod(callbackObj, progressMid, percentage, jName);
        env->PopLocalFrame(NULL);
    }
    
    // Final progress update
    jstring doneMsg = env->NewStringUTF("Extraction Finished");
    env->CallVoidMethod(callbackObj, progressMid, 100, doneMsg);
}
}
