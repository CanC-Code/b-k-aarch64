#include <jni.h>
#include <android/asset_manager_jni.h>
#include <vector>
#include <cstdint>
#include "otr_generator.hpp"
#include "otr_assets.hpp" // your embedded ROM/YAML headers

extern "C" {

// JNI: Load embedded ROM and YAML assets and generate OTR
JNIEXPORT jboolean JNICALL
Java_com_bkawrapper_NativeBridge_loadEmbeddedOTRAssets(JNIEnv* env, jclass clazz,
                                                      jobject activity,
                                                      jobject assetManager,
                                                      jobject progressCallback) {
    AAssetManager* mgr = AAssetManager_fromJava(env, assetManager);
    if (!mgr) return JNI_FALSE;

    OTRGenerator generator;
    generator.setProgressCallback([env, progressCallback](float p) {
        jclass cls = env->GetObjectClass(progressCallback);
        jmethodID mid = env->GetMethodID(cls, "onProgress", "(F)V");
        if (mid) env->CallVoidMethod(progressCallback, mid, p);
    });

    std::vector<uint8_t> outOTR;
    bool success = generator.generateOTR(
            embedded_rom, embedded_rom_size,
            reinterpret_cast<const char*>(embedded_us_yaml),
            embedded_us_yaml_size,
            outOTR
    );

    return success ? JNI_TRUE : JNI_FALSE;
}
}