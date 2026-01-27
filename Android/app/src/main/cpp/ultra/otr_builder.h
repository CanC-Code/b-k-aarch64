#ifndef OTR_BUILDER_H
#define OTR_BUILDER_H

#include <jni.h>
#include <cstdint>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Detects the ROM version (US, PAL, JP) based on the header bytes.
 * Returns a version constant used to select the correct manifest.
 */
int detect_rom_version(const uint8_t* romData, size_t size);

/**
 * Orchestrates the extraction of assets from the ROM into OTR files.
 * Replaces the functionality of rareunzip.py, splat_inputs.py, and generate_asset_enums.py.
 * * @param env The JNI Environment pointer.
 * @param activity The global reference to MainActivity for UI callbacks.
 * @param progressMid The cached method ID for MainActivity.updateOtrProgress.
 * @param romFd The file descriptor for the ROM file.
 * @param manifestPtr Pointer to the manifest.bin loaded from APK assets.
 * @param outDirPath The internal storage path to save the OTR files.
 */
void run_native_otr_generation_with_callback(JNIEnv* env, jobject activity, jmethodID progressMid,
                                           int romFd, uint8_t* manifestPtr, const char* outDirPath);

#ifdef __cplusplus
}
#endif

#endif // OTR_BUILDER_H
