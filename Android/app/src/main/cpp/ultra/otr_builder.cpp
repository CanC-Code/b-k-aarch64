#include "otr_builder.h"
#include <android/log.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
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
    
    if (manifestPtr == nullptr || manifestSize < 48) {
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Invalid manifest data");
        return;
    }

    uint32_t entryCount = manifestSize / 48;
    __android_log_print(ANDROID_LOG_INFO, LOG_TAG, "Starting OTR for %u entries", entryCount);

    for (uint32_t i = 0; i < entryCount; i++) {
        uint8_t* record = manifestPtr + (i * 48);
        
        // Safety check to ensure we aren't reading out of bounds
        if ((i * 48) + 48 > manifestSize) break;

        uint32_t romOffset = *(uint32_t*)(record + 0);
        uint32_t fileSize  = *(uint32_t*)(record + 4);
        
        // Ensure name is null-terminated for NewStringUTF
        char fileName[33];
        memcpy(fileName, record + 8, 32);
        fileName[32] = '\0'; 
        
        // Calculate percentage
        int percentage = (int)((i * 100) / entryCount);

        // CRASH PROTECTION: Check if env and activity are still valid
        if (env != nullptr && activity != nullptr && progressMid != nullptr) {
            jstring statusMsg = env->NewStringUTF(fileName);
            env->CallVoidMethod(activity, progressMid, percentage, statusMsg);
            
            // Critical: Clean up the local reference or it will overflow the JNI table
            env->DeleteLocalRef(statusMsg);
        }

        // --- Actual Processing Placeholder ---
        // usleep(1000); // Small sleep to prevent UI thread choking during testing
    }

    // Final Update
    if (env != nullptr && activity != nullptr) {
        jstring finishedMsg = env->NewStringUTF("Done");
        env->CallVoidMethod(activity, progressMid, 100, finishedMsg);
        env->DeleteLocalRef(finishedMsg);
    }
}

} // extern "C"
