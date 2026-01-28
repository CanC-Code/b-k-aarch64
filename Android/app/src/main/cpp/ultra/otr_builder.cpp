#include "otr_builder.h"
#include <android/log.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define LOG_TAG "OtrBuilder"

static JavaVM* g_vm = nullptr;

extern "C" {

void otr_builder_set_jvm(JavaVM* vm) {
    g_vm = vm;
}

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, uint32_t manifestSize, 
                                           const char* outDirPath) {
    
    // 1. Calculate entry count (48 bytes per entry)
    // We assume the manifest is a raw sequence of 48-byte structs
    uint32_t entryCount = manifestSize / 48;
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Starting OTR for %u entries", entryCount);

    for (uint32_t i = 0; i < entryCount; i++) {
        // Calculate pointer to current 48-byte record
        uint8_t* record = manifestPtr + (i * 48);
        
        // Extract 48-byte record data (Little Endian assumed from Python script)
        uint32_t romOffset = *(uint32_t*)(record + 0);
        uint32_t fileSize  = *(uint32_t*)(record + 4);
        char fileName[32];
        memcpy(fileName, record + 8, 32);
        // record + 40 to 48 is Type/Padding
        
        // 2. Report Progress back to Java
        int percentage = (int)((i * 100) / entryCount);
        jstring statusMsg = env->NewStringUTF(fileName);
        env->CallVoidMethod(activity, progressMid, percentage, statusMsg);
        env->DeleteLocalRef(statusMsg);

        // 3. Logic: pread from ROM FD using manifest data
        // uint8_t* buffer = (uint8_t*)malloc(fileSize);
        // pread(romFd, buffer, fileSize, romOffset);
        // ... call rare_decompression or OTR logic here ...
        // free(buffer);
    }

    // Final 100% update
    jstring finishedMsg = env->NewStringUTF("Done");
    env->CallVoidMethod(activity, progressMid, 100, finishedMsg);
    env->DeleteLocalRef(finishedMsg);
}

} // extern "C"
