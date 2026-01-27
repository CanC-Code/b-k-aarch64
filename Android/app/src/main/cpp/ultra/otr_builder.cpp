#include "otr_builder.h"
#include "assets_manifest.h"
#include "../tools/rare_decompression.h"
#include <vector>
#include <thread>
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <android/log.h>

#define LOG_TAG "OTR_BUILDER"
static JavaVM* g_jvm = nullptr;

void otr_builder_set_jvm(JavaVM* vm) { g_jvm = vm; }

void process_asset(int romFd, AssetEntry asset, const char* outDirPath) {
    char path[512];
    snprintf(path, sizeof(path), "%s/%s", outDirPath, asset.name);

    std::vector<uint8_t> comp(asset.compSize);
    if (pread(romFd, comp.data(), asset.compSize, asset.romOffset) < (ssize_t)asset.compSize) return;

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

    if (header->magic != 0x424B414D) { // 'BKAM'
        __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, "Manifest Magic Mismatch!");
        return;
    }

    AssetEntry* entries = (AssetEntry*)(manifestPtr + sizeof(ManifestHeader));

    // Parallel processing in batches of 4
    for (uint32_t i = 0; i < header->entryCount; i += 4) {
        std::vector<std::thread> workers;
        for (int t = 0; t < 4 && (i + t) < header->entryCount; t++) {
            workers.emplace_back(process_asset, romFd, entries[i + t], outDirPath);
        }
        for (auto& w : workers) if (w.joinable()) w.join();

        // Safe JNI update from background thread
        JNIEnv* myEnv;
        if (g_jvm->AttachCurrentThread(&myEnv, NULL) == JNI_OK) {
            int percent = (int)((float)(i + 1) / header->entryCount * 100.0f);
            jstring jName = myEnv->NewStringUTF(entries[i].name);
            myEnv->CallVoidMethod(activity, progressMid, percent, jName);
            myEnv->DeleteLocalRef(jName);
            g_jvm->DetachCurrentThread();
        }
    }
}
