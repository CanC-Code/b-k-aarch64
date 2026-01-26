// File: Android/app/src/main/cpp/ultra/otr_builder.cpp
#include <jni.h>
#include <android/log.h>
#include <stdio.h>

#define LOG_TAG "OTR_BUILDER"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C" {

void core1_loadOTR(int fd) {
    LOGI("Received ROM File Descriptor: %d", fd);
    
    // This is where the extraction logic starts.
    // For now, we wrap the FD in a FILE stream to test readability.
    FILE* romFile = fdopen(fd, "rb");
    if (romFile) {
        LOGI("ROM file opened successfully. Starting OTR generation...");
        // Extraction loop would go here
        fclose(romFile);
    } else {
        LOGI("Failed to open ROM from File Descriptor.");
    }
}

}
