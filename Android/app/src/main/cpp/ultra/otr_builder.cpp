#include "otr_builder.h"
#include <android/log.h>
#include <string.h>
#include <stdlib.h>

#define LOG_TAG "OtrBuilder"

static JavaVM* g_vm = nullptr;

extern "C" {

void otr_builder_set_jvm(JavaVM* vm) {
    g_vm = vm;
}

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, uint32_t manifestSize, 
                                           const char* outDirPath) {
    
    if (!manifestPtr || manifestSize < 48) return;

    uint32_t entryCount = manifestSize / 48;
    
    for (uint32_t i = 0; i < entryCount; i++) {
        // 1. Manage JNI local references to prevent overflow crash
        if (env->PushLocalFrame(10) < 0) break; 

        uint8_t* record = manifestPtr + (i * 48);
        char fileName[33];
        memcpy(fileName, record + 8, 32);
        fileName[32] = '\0';

        int percentage = (int)((i * 100) / entryCount);

        // 2. Call Java
        jstring jName = env->NewStringUTF(fileName);
        env->CallVoidMethod(activity, progressMid, percentage, jName);

        // 3. Pop the frame (automatically deletes jName)
        env->PopLocalFrame(NULL);
    }

    // Final Update
    jstring doneMsg = env->NewStringUTF("Done");
    env->CallVoidMethod(activity, progressMid, 100, doneMsg);
}

} // extern "C"
