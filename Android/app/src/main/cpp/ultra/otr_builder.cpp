#include "otr_builder.h"
#include <android/log.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>  // Added to fix 'undeclared identifier memcpy'
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
    
    // Calculate entry count based on the 48-byte struct logic
    uint32_t entryCount = manifestSize / 48;
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Starting OTR for %u entries", entryCount);

    for (uint32_t i = 0; i < entryCount; i++) {
        uint8_t* record = manifestPtr + (i * 48);
        
        // Offset (4), Size (4), Name (32), Type (8)
        uint32_t romOffset = *(uint32_t*)(record + 0);
        uint32_t fileSize  = *(uint32_t*)(record + 4);
        
        char fileName[33]; // 32 + null terminator
        memcpy(fileName, record + 8, 32);
        fileName[32] = '\0'; 
        
        // Report Progress back to Java UI
        int percentage = (int)((i * 100) / entryCount);
        jstring statusMsg = env->NewStringUTF(fileName);
        env->CallVoidMethod(activity, progressMid, percentage, statusMsg);
        env->DeleteLocalRef(statusMsg);

        // Actual extraction logic would go here:
        // pread(romFd, some_buffer, fileSize, romOffset);
    }

    // Signal completion
    jstring finishedMsg = env->NewStringUTF("Done");
    env->CallVoidMethod(activity, progressMid, 100, finishedMsg);
    env->DeleteLocalRef(finishedMsg);
}

} // extern "C"
