#include "otr_builder.h"
#include <android/log.h>
#include <string.h>

extern "C" {
static JavaVM* g_vm = nullptr;
void otr_builder_set_jvm(JavaVM* vm) { g_vm = vm; }

void run_native_otr_generation_with_callback(JNIEnv* env, jobject callbackObj, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, uint32_t manifestSize, 
                                           const char* outDirPath) {
    
    uint32_t entryCount = manifestSize / 48;

    for (uint32_t i = 0; i < entryCount; i++) {
        // PREVENT CRASH: Push a local frame to clean up strings automatically
        if (env->PushLocalFrame(10) < 0) return;

        uint8_t* record = manifestPtr + (i * 48);
        char fileName[33];
        memcpy(fileName, record + 8, 32);
        fileName[32] = '\0';

        int percentage = (int)((i * 100) / entryCount);
        jstring jName = env->NewStringUTF(fileName);
        
        // Call the Service's update method
        env->CallVoidMethod(callbackObj, progressMid, percentage, jName);

        env->PopLocalFrame(NULL); // Cleans up jName immediately
    }
}
}
