#ifndef OTR_BUILDER_H
#define OTR_BUILDER_H

#include <jni.h>
#include <stdint.h>

// Define the structures missing in your previous build[span_3](end_span)
struct AssetEntry {
    char name[256];
    uint32_t romOffset;
    uint32_t compSize;
    uint32_t type; 
};

struct ManifestHeader {
    uint32_t entryCount;
};

#define ASSET_TYPE_SKIP 0

void otr_builder_set_jvm(JavaVM* vm);
void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, const char* outDirPath);

#endif