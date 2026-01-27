#include "otr_builder.h"
#include <thread>
#include <vector>
#include <android/log.h>

static JavaVM* g_jvm = nullptr;

void otr_builder_set_jvm(JavaVM* vm) {
    g_jvm = vm;
}

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, const char* outDirPath) {
    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));
    
    // Create a global reference to the activity so background threads can find it
    jobject globalActivity = env->NewGlobalRef(activity);

    for (uint32_t i = 0; i < header->entryCount; i += 4) {
        // ... (Process assets in threads) ...
        
        // Reporting progress safely
        JNIEnv* myEnv;
        if (g_jvm->GetEnv((void**)&myEnv, JNI_VERSION_1_6) == JNI_EDETACHED) {
            g_jvm->AttachCurrentThread(&myEnv, NULL);
            
            int percent = (int)((float)(i) / header->entryCount * 100.0f);
            jstring jName = myEnv->NewStringUTF(entries[i].name);
            myEnv->CallVoidMethod(globalActivity, progressMid, percent, jName);
            myEnv->DeleteLocalRef(jName);
            
            g_jvm->DetachCurrentThread();
        }
    }
    
    env->DeleteGlobalRef(globalActivity);
}
