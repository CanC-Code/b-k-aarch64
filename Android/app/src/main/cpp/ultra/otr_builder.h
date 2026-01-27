#ifndef OTR_BUILDER_H
#define OTR_BUILDER_H

#include <jni.h>
#include <stdint.h>

// Removed duplicate AssetEntry and ManifestHeader structs
// These are now exclusively defined in assets_manifest.h

void otr_builder_set_jvm(JavaVM* vm);

void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, const char* outDirPath);

#endif
