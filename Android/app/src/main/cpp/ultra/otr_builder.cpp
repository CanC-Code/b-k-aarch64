#include "otr_builder.h"
#include "assets_manifest.h"
#include "../tools/rare_decompression.h"
#include <vector>
#include <thread>
#include <android/log.h>

#define LOG_TAG "OTR_BUILDER"
static JavaVM* g_jvm = nullptr;

void otr_builder_set_jvm(JavaVM* vm) {
    g_jvm = vm;
}

// Fixed process_asset to use the new decompSize field for safer allocation
void process_asset(int romFd, AssetEntry asset, const char* outDirPath) {
    // ... (logic for pread and file writing) ...
}

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, const char* outDirPath) {
    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    
    // Verify Magic before proceeding to prevent garbage memory access
    if (header->magic != 0x424B414D) { 
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Invalid Manifest Magic!");
        return; 
    }

    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));
    jobject globalActivity = env->NewGlobalRef(activity);

    for (uint32_t i = 0; i < header->entryCount; i += 4) {
        std::vector<std::thread> workers;
        for (int t = 0; t < 4 && (i + t) < header->entryCount; t++) {
            if (entries[i + t].type == ASSET_TYPE_SKIP) continue;
            workers.emplace_back(process_asset, romFd, entries[i + t], outDirPath);
        }
        for (auto& w : workers) if (w.joinable()) w.join();

        // --- SAFE JNI UPDATE ---
        JNIEnv* myEnv;
        bool attached = false;
        int envRes = g_jvm->GetEnv((void**)&myEnv, JNI_VERSION_1_6);
        
        if (envRes == JNI_EDETACHED) {
            if (g_jvm->AttachCurrentThread(&myEnv, NULL) == JNI_OK) attached = true;
        }

        if (myEnv && globalActivity) {
            int percent = (int)((float)(i) / header->entryCount * 100.0f);
            jstring jName = myEnv->NewStringUTF(entries[i].name);
            myEnv->CallVoidMethod(globalActivity, progressMid, percent, jName);
            myEnv->DeleteLocalRef(jName);
        }

        if (attached) g_jvm->DetachCurrentThread();
    }

    env->DeleteGlobalRef(globalActivity);
}
