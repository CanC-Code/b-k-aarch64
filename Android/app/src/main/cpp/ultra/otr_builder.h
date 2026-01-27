#ifndef OTR_BUILDER_H
#define OTR_BUILDER_H

#include <jni.h>
#include <cstdint>

#ifdef __cplusplus
extern "C" {
#endif

int detect_rom_version(const uint8_t* romData, size_t size);

// Note: Added JNIEnv and jobject to the signature
void extract_assets_to_otr(JNIEnv* env, jobject activity, const uint8_t* romData, size_t size);

#ifdef __cplusplus
}
#endif

#endif
