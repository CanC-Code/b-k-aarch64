#include "otr_builder.h"
#include "assets_manifest.h"
#include <vector>
#include <thread>
#include <android/log.h>

#define LOG_TAG "OTR_BUILDER"
static JavaVM* g_jvm = nullptr;

void otr_builder_set_jvm(JavaVM* vm) { g_jvm = vm; }

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, const char* outDirPath) {
    
    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));

    for (uint32_t i = 0; i < header->entryCount; i++) {
        // ... (extraction logic) ...

        // FIX: Safe JNI update from background thread
        JNIEnv* localEnv;
        if (g_jvm->AttachCurrentThread(&localEnv, NULL) == JNI_OK) {
            int percent = (int)((float)i / header->entryCount * 100.0f);
            jstring jName = localEnv->NewStringUTF(entries[i].name);
            
            localEnv->CallVoidMethod(activity, progressMid, percent, jName);
            
            localEnv->DeleteLocalRef(jName);
            g_jvm->DetachCurrentThread();
        }
    }
}
