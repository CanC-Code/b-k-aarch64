#include "otr_builder.h"
#include "assets_manifest.h"
#include "../tools/rare_decompression.h"
#include <vector>
#include <thread>
#include <mutex>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <android/log.h>

#define LOG_TAG "OTR_BUILDER"
#define LOGD(...) __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, __VA_ARGS__)

// We need the Global JavaVM to attach threads
JavaVM* g_jvm = nullptr;

// Add this to capture the JVM when the library loads or init is called
JNIEXPORT jint JNI_OnLoad(JavaVM* vm, void* reserved) {
    g_jvm = vm;
    return JNI_VERSION_1_6;
}

void process_asset(int romFd, AssetEntry& asset, const char* outDirPath) {
    char path[512];
    snprintf(path, sizeof(path), "%s/%s", outDirPath, asset.name);

    struct stat st;
    if (stat(path, &st) == 0 && st.st_size > 0) return; 

    std::vector<uint8_t> comp(asset.compSize);
    pread(romFd, comp.data(), asset.compSize, asset.romOffset);

    uint32_t outSize = 0;
    uint8_t* decomp = decompress_rare_asset(comp.data(), asset.compSize, &outSize);

    if (decomp) {
        int out = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0666);
        if (out != -1) {
            write(out, decomp, outSize);
            close(out);
        }
        free(decomp);
    }
}

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, const char* outDirPath) {
    mkdir(outDirPath, 0777);
    
    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));

    // Make activity a global ref so worker threads can see it
    jobject globalActivity = env->NewGlobalRef(activity);

    const int batchSize = 4;
    for (uint32_t i = 0; i < header->entryCount; i += batchSize) {
        std::vector<std::thread> workers;

        for (int t = 0; t < batchSize && (i + t) < header->entryCount; t++) {
            if (entries[i + t].type == ASSET_TYPE_SKIP) continue;
            workers.emplace_back(process_asset, romFd, std::ref(entries[i + t]), outDirPath);
        }

        for (auto& w : workers) {
            if (w.joinable()) w.join();
        }

        // --- CRITICAL FIX: Ensure we are attached to the JVM for the callback ---
        JNIEnv* localEnv;
        bool attached = false;
        if (g_jvm->GetEnv((void**)&localEnv, JNI_VERSION_1_6) == JNI_EDETACHED) {
            g_jvm->AttachCurrentThread(&localEnv, NULL);
            attached = true;
        }

        if (localEnv && globalActivity && progressMid) {
            int percent = (int)((float)(i + 1) / header->entryCount * 100.0f);
            jstring jName = localEnv->NewStringUTF(entries[i].name);
            localEnv->CallVoidMethod(globalActivity, progressMid, percent, jName);
            localEnv->DeleteLocalRef(jName);
        }

        if (attached) g_jvm->DetachCurrentThread();
    }

    env->DeleteGlobalRef(globalActivity);
}
