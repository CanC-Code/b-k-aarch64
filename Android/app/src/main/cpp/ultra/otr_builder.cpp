#include "otr_builder.h"
#include <vector>
#include <thread>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <android/log.h>

#define LOG_TAG "OTR_BUILDER"

static JavaVM* g_jvm = nullptr;

void otr_builder_set_jvm(JavaVM* vm) {
    g_jvm = vm;
}

void process_asset(int romFd, AssetEntry& asset, const char* outDirPath) {
    char path[512];
    snprintf(path, sizeof(path), "%s/%s", outDirPath, asset.name);
    
    struct stat st;
    if (stat(path, &st) == 0 && st.st_size > 0) return; 

    std::vector<uint8_t> comp(asset.compSize);
    if (pread(romFd, comp.data(), asset.compSize, asset.romOffset) < (ssize_t)asset.compSize) return;

    // Assume decompress_rare_asset is defined elsewhere in your tools
    uint32_t outSize = 0;
    extern uint8_t* decompress_rare_asset(uint8_t*, uint32_t, uint32_t*);
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
    
    struct ManifestHeader { uint32_t entryCount; }; 
    ManifestHeader* header = (ManifestHeader*)manifestPtr;
    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));

    const int batchSize = 4;
    for (uint32_t i = 0; i < header->entryCount; i += batchSize) {
        std::vector<std::thread> workers;
        for (int t = 0; t < batchSize && (i + t) < header->entryCount; t++) {
            workers.emplace_back(process_asset, romFd, std::ref(entries[i + t]), outDirPath);
        }

        for (auto& w : workers) if (w.joinable()) w.join();

        // ATTACH THREAD TO JVM FOR CALLBACK
        JNIEnv* myEnv;
        bool attached = false;
        if (g_jvm->GetEnv((void**)&myEnv, JNI_VERSION_1_6) == JNI_EDETACHED) {
            if (g_jvm->AttachCurrentThread(&myEnv, NULL) == JNI_OK) attached = true;
        }

        if (myEnv && activity && progressMid) {
            int percent = (int)((float)(i + 1) / header->entryCount * 100.0f);
            jstring jName = myEnv->NewStringUTF(entries[i].name);
            myEnv->CallVoidMethod(activity, progressMid, percent, jName);
            myEnv->DeleteLocalRef(jName);
        }

        if (attached) g_jvm->DetachCurrentThread();
    }
}
